# Prompt Compression and Token Budgeting using LLMLingua

A research prototype for question-aware prompt compression and token-budget enforcement on enterprise logs and multi-page PDFs. The benchmark is designed to run locally with open-source models; no paid API key is required.

## Local model setup (₹0 API usage)

1. Install [Ollama](https://ollama.com/) for your operating system and start it.
2. Download a local instruction model. A small starting point is:

```bash
ollama pull qwen2.5:3b
```

3. Configure the benchmark environment:

Windows PowerShell:
```powershell
$env:LLM_BASE_URL="http://localhost:11434/v1"
$env:LLM_MODEL="qwen2.5:3b"
$env:LLM_API_KEY="ollama"
```

macOS/Linux:
```bash
export LLM_BASE_URL="http://localhost:11434/v1"
export LLM_MODEL="qwen2.5:3b"
export LLM_API_KEY="ollama"
```

The API key value is a local placeholder accepted by Ollama's OpenAI-compatible endpoint; it is not an OpenAI credential and does not incur API charges. The model runs on your machine, so speed depends on available RAM/VRAM and hardware.

## Setup

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev,compression]"
```

LLMLingua downloads its configured compressor model from Hugging Face on first use. This download is separate from Ollama and may require substantial RAM/VRAM. The default compressor is `microsoft/llmlingua-2-xlm-roberta-large-meetingbank`. For middleware-only development, set `compression.use_llmlingua: false` in `configs/default.yaml`.

## Run the API

```bash
uvicorn prompt_budget.api:app --reload
```

POST JSON to `/compress` with `question`, `context`, optional `system_instruction`, `target_ratio`, `token_budget`, and `task`.

## Run tests

```bash
pytest -q
```

## Run the model-backed benchmark

Keep Ollama running in another terminal, then:

```bash
python benchmarks/run_benchmark.py --input data/benchmark.example.jsonl
```

The benchmark runner sends each compressed prompt to the configured local model. The sample JSONL cases are illustrative only; replace them with curated, labelled cases before reporting experimental results. The configured cost rates are zero for local inference, but report hardware and model details because local compute still has an electricity and time cost.

## Current implementation

- PDF, text, log, Markdown, CSV, and JSONL ingestion utilities.
- Token-window chunking and question-term relevance ranking.
- LLMLingua compression applied to context only; system instruction and question are preserved.
- Configurable token budget and per-request JSONL telemetry.
- FastAPI compression endpoint.
- Exact Match, token F1, and ROUGE-L metric utilities.
- Model-backed benchmark runner with local OpenAI-compatible inference client.

## Experimental plan

Compare 1x, 2x, 3x, and 5x on summarization, extractive QA, and multi-hop QA, with three runs per cell. Keep the downstream model, compressor model, dataset split, chunking configuration, prompt template, and decoding settings fixed across ratios. Record prompt tokens, compression latency, inference latency, end-to-end latency, and quality metrics. Derive safe compression thresholds only from measured held-out task quality.

## Project layout

- `src/prompt_budget/`: configuration, ingestion, chunking, compressor adapter, middleware, telemetry, API and LLM client.
- `benchmarks/`: evaluation metrics and runner.
- `configs/`: model and experiment settings.
- `data/`: illustrative benchmark case.
- `tests/`: regression tests.
- `docs/`: experimental methodology.

## Known limitations

- Chunk ranking is lexical overlap, not semantic retrieval.
- Token-budget enforcement is applied after compression by truncating context; it never truncates the system instruction or question.
- Local model token usage may not be returned by every OpenAI-compatible server; check telemetry fields for missing usage values.
- The included example data is not empirical evidence. A curated benchmark dataset and repeated experiments are required for conclusions.
