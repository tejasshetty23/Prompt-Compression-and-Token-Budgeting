"""FastAPI endpoints for the compression middleware and its web frontend."""
import csv
import json
import math
import os
import tempfile
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import AppConfig, load_config
from .ingestion import read_text
from .llm_client import ChatCompletionClient
from .middleware import PromptBudgetMiddleware
from .tokenization import count_tokens

ROOT = Path.cwd()
SUPPORTED_UPLOADS = {".pdf", ".txt", ".log", ".md", ".csv", ".json", ".jsonl"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


class CompressRequest(BaseModel):
    system_instruction: str = "You are a helpful assistant."
    question: str
    context: str
    target_ratio: float = Field(2.0, ge=1)
    token_budget: int | None = Field(None, ge=1)
    task: str = "unspecified"


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(CompressRequest):
    model: str | None = None
    temperature: float = Field(0.0, ge=0, le=2)
    history: list[ChatTurn] = []


app = FastAPI(title="Prompt Budget Middleware", version="0.1.0")
try:
    config = load_config("configs/default.yaml")
except FileNotFoundError:
    config = AppConfig()
middleware = PromptBudgetMiddleware(config)
llm = ChatCompletionClient()
# LLMLingua loads lazily and is not safe to load twice concurrently.
_compress_lock = threading.Lock()


def _preload_compressor():
    """Load LLMLingua-2 in the background so the first chat isn't a minute slow."""
    if not (config.compression.enabled and config.compression.use_llmlingua):
        return
    with _compress_lock:
        try:
            middleware.compressor._load()
        except RuntimeError:
            pass  # surfaced to the user on the first compression request


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    if os.getenv("PROMPT_BUDGET_PRELOAD", "1") != "0":
        threading.Thread(target=_preload_compressor, daemon=True).start()
    yield


app.router.lifespan_context = _lifespan


def _prepare(request: CompressRequest):
    with _compress_lock:
        return middleware.prepare(
            system_instruction=request.system_instruction,
            question=request.question,
            context=request.context,
            target_ratio=request.target_ratio,
            token_budget=request.token_budget,
            task=request.task,
        )


def _public_metadata(metadata: dict) -> dict:
    """Drop the duplicated compressed prompt from LLMLingua's raw report."""
    meta = dict(metadata)
    reported = meta.get("reported")
    if isinstance(reported, dict):
        meta["reported"] = {k: v for k, v in reported.items() if k != "compressed_prompt"}
    return meta


@app.post("/compress")
def compress(request: CompressRequest):
    try:
        result = _prepare(request)
        return {"prompt": result.prompt, "context": result.context,
                "telemetry": result.telemetry.to_dict(),
                "compressor_metadata": result.compressor_metadata}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------- /api routes

@app.get("/api/health")
def health():
    try:
        models = llm.list_models()
        llm_status = {"reachable": True, "models": models}
    except RuntimeError as exc:
        llm_status = {"reachable": False, "models": [], "error": str(exc)}
    c = config.compression
    return {
        "status": "ok",
        "llm": {"base_url": llm.base_url, "default_model": llm.model, **llm_status},
        "compressor": {
            "model_name": c.model_name,
            "use_llmlingua": c.use_llmlingua,
            "loaded": middleware.compressor._model is not None,
        },
        "config": {
            "target_ratio": c.target_ratio,
            "chunk_size_tokens": c.chunk_size_tokens,
            "chunk_overlap_tokens": c.chunk_overlap_tokens,
            "top_k_chunks": c.top_k_chunks,
            "adaptive_control": c.adaptive_control,
            "tolerance": c.tolerance,
            "encoding_name": config.tokenizer.encoding_name,
            "ratios": config.benchmark.ratios,
        },
    }


@app.post("/api/compress")
def api_compress(request: CompressRequest):
    try:
        result = _prepare(request)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"prompt": result.prompt, "context": result.context,
            "telemetry": result.telemetry.to_dict(),
            "compressor_metadata": _public_metadata(result.compressor_metadata)}


@app.post("/api/tokens")
def api_tokens(payload: dict):
    text = str(payload.get("text", ""))
    return {"tokens": count_tokens(text, config.tokenizer.encoding_name)}


@app.post("/api/chat")
def api_chat(request: ChatRequest):
    """Compress the context, then stream the model answer as NDJSON events."""

    def events():
        def emit(obj):
            return json.dumps(obj, default=str) + "\n"

        yield emit({"type": "status", "stage": "compressing"})
        try:
            result = _prepare(request)
        except (ValueError, RuntimeError) as exc:
            yield emit({"type": "error", "stage": "compression", "message": str(exc)})
            return
        yield emit({
            "type": "compression",
            "context": result.context,
            "telemetry": result.telemetry.to_dict(),
            "compressor_metadata": _public_metadata(result.compressor_metadata),
        })
        yield emit({"type": "status", "stage": "generating"})
        try:
            for kind, value in llm.stream_answer(
                request.system_instruction, request.question, result.context,
                temperature=request.temperature,
                history=[t.model_dump() for t in request.history],
                model=request.model,
            ):
                if kind == "token":
                    yield emit({"type": "token", "text": value})
                else:
                    yield emit({"type": "done", "llm": value})
        except (RuntimeError, ValueError, OSError) as exc:
            yield emit({"type": "error", "stage": "generation", "message": str(exc)})

    return StreamingResponse(events(), media_type="application/x-ndjson")


@app.post("/api/ingest")
async def api_ingest(request: Request, filename: str = Query(..., min_length=1)):
    """Accept a raw file body and return its extracted text."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_UPLOADS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {suffix or 'none'}")
    body = await request.body()
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 25 MB")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ("upload" + suffix)
        path.write_bytes(body)
        try:
            text = read_text(path)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"filename": filename, "text": text,
            "tokens": count_tokens(text, config.tokenizer.encoding_name)}


@app.get("/api/samples")
def api_samples(limit: int = Query(6, ge=1, le=60)):
    path = ROOT / "data" / "benchmark.jsonl"
    if not path.exists():
        return {"samples": []}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    # Spread picks across the three task families.
    by_task: dict[str, list] = {}
    for row in rows:
        by_task.setdefault(row["task"], []).append(row)
    picks, i = [], 0
    while len(picks) < limit and any(i < len(v) for v in by_task.values()):
        for task_rows in by_task.values():
            if i < len(task_rows) and len(picks) < limit:
                picks.append(task_rows[i])
        i += 1
    return {"samples": picks}


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            clean = {}
            for key, value in row.items():
                if value in ("", None):
                    clean[key] = None
                    continue
                try:
                    number = float(value)
                    clean[key] = None if math.isnan(number) else number
                except ValueError:
                    clean[key] = value
            out.append(clean)
    return out


@app.get("/api/benchmarks")
def api_benchmarks():
    figures_dir = ROOT / "artifacts" / "figures"
    figures = sorted(p.name for p in figures_dir.glob("*.png")) if figures_dir.exists() else []
    return {
        "summary": _read_csv(ROOT / "artifacts" / "benchmark_summary.csv"),
        "figures": [f"/api/figures/{name}" for name in figures],
    }


@app.get("/api/figures/{name}")
def api_figure(name: str):
    path = (ROOT / "artifacts" / "figures" / name).resolve()
    figures_dir = (ROOT / "artifacts" / "figures").resolve()
    if path.parent != figures_dir or path.suffix != ".png" or not path.exists():
        raise HTTPException(status_code=404, detail="Figure not found")
    return FileResponse(path)


# Serve the built frontend (frontend/dist) when present.
_dist = ROOT / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
