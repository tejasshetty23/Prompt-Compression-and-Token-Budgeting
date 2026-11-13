# Benchmark Methodology and Experimental Design

## 1. Experimental Design

The benchmark uses 60 curated synthetic incident cases: 20 Extractive QA, 20 Multi-Hop QA, and 20 Incident Summarization cases. Each case is evaluated once at target ratios 1x, 2x, 3x, and 5x, producing 240 rows. These are not repeated trials.

## 2. Controlled Configuration

- Downstream model: `qwen2.5:1.5b` for all 240 recorded rows.
- Runtime: Ollama local generation API.
- Decoding: temperature 0.0, top-p 1.0, stream false (as confirmed by the benchmark operator).
- Model metadata: Qwen2 architecture, Q4_K_M quantization, 32,768 native context, 1,536 embedding dimension.
- Benchmark context limit: 4,096 tokens.
- Compressor: `microsoft/llmlingua-2-xlm-roberta-large-meetingbank`.
- Hardware: Apple M2 MacBook Air, 8 CPU cores, 8 GB RAM, ARM64, macOS 26.6.2.
- Reported software: Python 3.13.7, Ollama 0.40.11, PyTorch 2.6.0, Transformers 5.20.2, tiktoken 0.14.0, LLMLingua 0.2.2.
- PyTorch MPS was available. The benchmark CSV does not record whether compression used CPU or MPS; no device attribution is made.

## 3. Metrics

Actual compression ratio is original context tokens divided by compressed context tokens. Quality metrics are task-specific: Extractive QA uses exact match and token F1; Multi-Hop QA uses token F1, ROUGE-L, semantic similarity, and key-fact recall; summarization uses ROUGE-1/2/L and key-fact recall. System metrics are compression, inference, and end-to-end latency.

## 4. Statistical Interpretation

For each task and ratio, reported means and standard deviations describe variation across the 20 distinct benchmark cases. Because there is only one run per case/ratio, these standard deviations are not repeated-run uncertainty estimates. No confidence intervals or statistical significance claims are made.

## 5. Semantic Metric Provenance

The original CSV does not record the semantic-similarity backend. The implementation supports MiniLM embeddings and a token-Jaccard fallback. Historical semantic values therefore cannot be attributed exclusively to MiniLM. The benchmark runner was subsequently updated to record backend provenance for future runs.

## 6. Cost Interpretation

The local Ollama configuration records zero input and output token prices. Therefore, the experiment measures no commercial API dollar savings. Any cloud-cost scenario must be explicitly labeled hypothetical and based on stated external pricing assumptions.

## 7. Compression-Ratio Interpretation

Aggregate means align closely with target ratios, but per-case variation is material. Only 25/60 cases at 2x, 25/60 at 3x, and 27/60 at 5x fall within ±5% of target. These aggregate results do not establish a per-request ratio guarantee or a universally safe task threshold.
