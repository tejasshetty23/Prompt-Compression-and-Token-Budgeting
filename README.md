# Prompt Compression and Token Budgeting using LLMLingua

An enterprise-grade Python middleware and research benchmark for question-aware prompt compression and token-budget enforcement on telemetry logs, diagnostic traces, and multi-page technical documents.

Evaluated with **LLMLingua-2** (`microsoft/llmlingua-2-xlm-roberta-large-meetingbank`) and local open-source instruction models via **Ollama** (e.g., `Qwen 2.5 1.5B` / `Qwen 2.5 3B`) with zero external API fees.

---

## Key Features & Enhancements

1. **Calibrated Compression-Ratio Control**:
   - Eliminates LLMLingua-2's inherent overshooting (previously 5.8x–7.7x on requested 5.0x) using an empirical power-law calibration:
     $$r_0(R) = R^{-0.86}$$
   - Closed-loop adaptive proportional feedback controller with bounded single-step refinement ($\tau = 0.15$), delivering predictable compression within $\pm 5\%$ of target ratios.
2. **Context Isolation Invariant**:
   - System instructions and user questions are anchored as preserved invariants; compression operates strictly on context without mutating instructions or user queries.
3. **Comprehensive 60-Case Enterprise Benchmark Dataset**:
   - **20 Extractive QA** cases (`extract-001` to `extract-020`): precise entity and metric retrieval under compression.
   - **20 Multi-Hop QA** cases (`multi-001` to `multi-020`): multi-clause causal sequence and dependency reasoning.
   - **20 Incident Summarization** cases (`summary-001` to `summary-020`): cause, impact, resolution, and outcome retention.
   - Covers 9 enterprise infrastructure archetypes: Kubernetes, Kafka, PostgreSQL, Redis, CoreDNS, OAuth/IAM, gRPC microservices, CI/CD, and BGP/Cloud networking.
4. **Reliable Multimodal Evaluation Suite**:
   - Excluded model and compressor warm-ups.
   - Granular latency decomposition: Compression Latency vs Inference Latency vs End-to-End Latency.
   - Task-appropriate metrics: Exact Match, Token F1, ROUGE-1/2/L, Key Fact Recall, and Semantic similarity with explicit backend provenance (MiniLM when locally available; otherwise labelled token-Jaccard fallback).
   - Per-case and task-aggregated mean and standard deviation reporting.
5. **Ingestion & Token Budgeting Middleware**:
   - Ingestion utilities for `.log`, `.pdf` (via `pdfplumber`), `.txt`, `.md`, `.csv`, and `.jsonl`.
   - Lexical token-window chunking (800-token chunks with 80-token overlap) and question-overlap ranking.
   - Hard per-request token budget enforcement and JSONL telemetry.
   - FastAPI server endpoint (`/compress`).

---

## Architecture

```
[ Incoming Query & Context ]
           │
           ▼
┌──────────────────────────────────────────────┐
│        PromptBudgetMiddleware                │
│                                              │
│  1. Extract & Anchor Instructions & Question │
│  2. Token-Window Chunking & Lexical Ranking  │
│  3. LLMLingua-2 Calibrated Adaptive Compress │
│     ├── Initial Rate: r0 = R^(-0.86)         │
│     └── Adaptive Feedback Refinement         │
│  4. Token Budget Guard (Context Truncation)  │
│  5. Telemetry & Cost Recording               │
└──────────────────────────────────────────────┘
           │
           ▼
[ Compressed Prompt ] ──► [ Local Ollama Qwen 2.5 1.5B ] ──► [ Evaluation Metrics ]
```

---

## Setup Instructions

### 1. Environment & Dependencies

Python 3.10+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev,compression]"
```

*Note: The LLMLingua-2 compressor (`microsoft/llmlingua-2-xlm-roberta-large-meetingbank`) is downloaded from Hugging Face on first execution.*

### 2. Local LLM Setup (Ollama — ₹0 API Usage)

1. Install [Ollama](https://ollama.com/) and start the daemon.
2. Pull the target model:
   ```bash
   ollama pull qwen2.5:1.5b
   ```
3. Set environment variables:
   ```bash
   export LLM_BASE_URL="http://localhost:11434/v1"
   export LLM_MODEL="qwen2.5:1.5b"
   export LLM_API_KEY="ollama"
   ```

---

## Execution & Usage

### Running Tests
Execute unit tests for compression control, token budgeting, chunking, and invariants:
```bash
pytest -v
```

### Running the API Server
Start the FastAPI compression middleware:
```bash
uvicorn prompt_budget.api:app --reload
```
Send POST requests to `/compress` with:
```json
{
  "question": "Which service returned HTTP 503?",
  "context": "2026-10-01 09:00:07 ERROR inventory-service returned HTTP 503...",
  "target_ratio": 2.0,
  "token_budget": 500,
  "task": "extractive_qa"
}
```

### Running the Benchmark
Run the full 60-case benchmark across 1x, 2x, 3x, and 5x compression ratios:
```bash
python benchmarks/run_benchmark.py --input data/benchmark.jsonl --output artifacts/benchmark_results.csv --model qwen2.5:1.5b
```

### Generating Statistical Summaries
Compute task-level and case-level means and standard deviations:
```bash
python benchmarks/analyze_results.py --input artifacts/benchmark_results.csv --output artifacts/benchmark_summary.csv --case-output artifacts/benchmark_case_summary.csv
```

### Generating Research Figures
Generate accuracy, latency, configured-cost, and compression-ratio graphs:
```bash
python benchmarks/plot_results.py --input artifacts/benchmark_results.csv --output-dir artifacts/figures
```

---

## Repository Structure

```
├── configs/
│   └── default.yaml                 # Compression, tokenizer, cost & benchmark config
├── data/
│   ├── benchmark.jsonl              # 60 curated enterprise incident cases (20/task)
│   ├── build_benchmark_dataset.py   # Dataset builder script
│   └── documents/                   # Sample raw enterprise log and document inputs
├── docs/
│   ├── DATASET.md                   # Dataset specification, taxonomy & statistics
│   ├── METHODOLOGY.md               # Scientific methodology & control theory
│   ├── BENCHMARK_REPORT.md          # Comprehensive empirical benchmark findings
│   └── IEEE_RESEARCH_PAPER.md       # Complete 10-page academic research paper
├── benchmarks/
│   ├── run_benchmark.py             # Fault-tolerant model-backed benchmark runner
│   ├── analyze_results.py           # Statistical aggregation (mean, std)
│   ├── plot_results.py              # Publication figure generator
│   └── metrics.py                   # EM, Token F1, ROUGE-1/2/L, Semantic Similarity
├── src/prompt_budget/
│   ├── compressor.py                # LLMLingua-2 adapter with calibrated power-law control
│   ├── middleware.py                # Core prompt budgeting & isolation middleware
│   ├── chunking.py                  # Token-window chunking & question relevance ranking
│   ├── ingestion.py                 # File & PDF ingestion utilities
│   ├── tokenization.py              # Token counting & boundary truncation
│   ├── telemetry.py                 # Telemetry & cost logging
│   ├── llm_client.py                # Local OpenAI-compatible inference client
│   └── api.py                       # FastAPI REST service
└── tests/
    └── test_middleware.py           # Regression & unit test suite
```
