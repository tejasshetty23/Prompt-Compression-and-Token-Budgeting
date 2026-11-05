# Prompt Compression and Token Budgeting using LLMLingua

A research prototype for question-aware prompt compression and token-budget enforcement on enterprise logs and multi-page PDFs.

## Current implementation

- PDF, text, log, Markdown, CSV, and JSONL ingestion utilities.
- Token-window chunking and question-term relevance ranking.
- LLMLingua compression applied to context only; system instruction and question are preserved.
- Configurable token budget and per-request JSONL telemetry.
- FastAPI compression endpoint.
- Exact Match, token F1, and ROUGE-L metric utilities.
- Example benchmark input schema and unit tests.

## Setup

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

Install the actual compression model dependency separately when ready to run LLMLingua:

```bash
pip install -e ".[compression]"
```

The first compression call downloads the configured Hugging Face model. Model loading may require substantial RAM/VRAM. For middleware-only development, set `compression.use_llmlingua: false` in `configs/default.yaml`.

## Run the API

```bash
uvicorn prompt_budget.api:app --reload
```

POST JSON to `/compress` with `question`, `context`, optional `system_instruction`, `target_ratio`, `token_budget`, and `task`.

## Run tests

```bash
pytest -q
```

## Benchmark status

The benchmark runner currently evaluates predictions supplied in each JSONL case under `prediction_by_ratio`. It does not yet call a downstream LLM to generate predictions. The included example data is illustrative only and must not be presented as measured experimental evidence.

The experimental plan is to compare 1x, 2x, 3x, and 5x on summarization, extractive QA, and multi-hop QA, with three runs per cell. Record the downstream model, dataset split, compressor model, chunk size/overlap, decoding parameters, prompt tokens, compression latency, end-to-end latency, and estimated API cost. Derive safe compression thresholds only from measured held-out task quality.

## Project layout

- `src/prompt_budget/`: configuration, ingestion, chunking, compressor adapter, middleware, telemetry, API.
- `benchmarks/`: evaluation metrics and runner.
- `configs/`: model and experiment settings.
- `data/`: illustrative benchmark case.
- `tests/`: regression tests.
- `docs/`: experimental methodology.

## Known limitations

- Chunk ranking is lexical overlap, not semantic retrieval.
- Token-budget enforcement is applied after compression by truncating context; it never truncates the system instruction or question.
- Cost estimation currently uses configured input-token pricing; it does not include provider-specific discounts, cached tokens, or generated output.
- A downstream model adapter, curated benchmark data, repeated experiments, and report generation are still required.
