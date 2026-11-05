"""FastAPI endpoint for the compression middleware."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .config import AppConfig, load_config
from .middleware import PromptBudgetMiddleware

class CompressRequest(BaseModel):
    system_instruction: str = "You are a helpful assistant."
    question: str
    context: str
    target_ratio: float = Field(2.0, ge=1)
    token_budget: int | None = Field(None, ge=1)
    task: str = "unspecified"

app = FastAPI(title="Prompt Budget Middleware", version="0.1.0")
try:
    config = load_config("configs/default.yaml")
except FileNotFoundError:
    config = AppConfig()
middleware = PromptBudgetMiddleware(config)

@app.post("/compress")
def compress(request: CompressRequest):
    try:
        result = middleware.prepare(**request.model_dump())
        return {"prompt": result.prompt, "context": result.context,
                "telemetry": result.telemetry.to_dict(),
                "compressor_metadata": result.compressor_metadata}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
