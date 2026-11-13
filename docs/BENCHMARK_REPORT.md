# Benchmark Report: Prompt Compression and Token Budgeting with LLMLingua-2

**Evaluation artifact:** `artifacts/benchmark_results.csv`  
**Rows:** 240 (60 cases × 4 target ratios; one run per case/ratio)  
**Downstream model:** `qwen2.5:1.5b` (all 240 rows)  
**Dataset:** Curated synthetic incident cases; not production telemetry.

## 1. Executive Summary

The calibrated controller brings aggregate compression-ratio means close to requested targets, but per-case ratio deviations remain. Compression reduces prompt length and downstream inference time, but its several-second overhead increases end-to-end latency in this local setup. Quality generally declines with stronger compression, particularly for extractive QA and incident summarization.

No commercial API cost savings were measured: all recorded estimated cost fields are zero under the local Ollama configuration. The CSV contains one observation per case and ratio, so reported standard deviations describe variation across cases, not repeated-run uncertainty.

## 2. Experimental Environment

The benchmark machine was a MacBook Air (Mac14,2), Apple M2, 8 CPU cores, 8 GB RAM, ARM64, macOS 26.6.2. Reported installed versions: Python 3.13.7, Ollama 0.40.11, PyTorch 2.6.0, Transformers 5.20.2, tiktoken 0.14.0, and LLMLingua 0.2.2. PyTorch MPS was available, but the CSV does not record the compressor execution device; do not infer CPU or MPS from availability alone.

All 240 CSV rows identify `qwen2.5:1.5b`. Sushir reports Ollama `/api/generate` requests with temperature 0.0, top-p 1.0, and streaming disabled. Model metadata: Qwen2 architecture, approximately 1.54B parameters, Q4_K_M quantization, 32,768-token native context, 1,536 embedding dimension. Benchmark context limit: 4,096 tokens.

## 3. Compression-Ratio Control

| Target | Mean actual ratio | SD across cases | Within ±5% | Within ±15% |
|---:|---:|---:|---:|---:|
| 1.0x | 1.000 | 0.000 | 60/60 | 60/60 |
| 2.0x | 1.980 | 0.152 | 25/60 | 58/60 |
| 3.0x | 2.984 | 0.215 | 25/60 | 60/60 |
| 5.0x | 4.837 | 0.352 | 27/60 | 60/60 |

Aggregate alignment must not be described as a per-request ±5% guarantee.

## 4. Task Quality Results

Values are means across 20 cases per task and ratio. SDs are across cases.

### Extractive QA

| Target | Exact Match | Token F1 |
|---:|---:|---:|
| 1.0x | 0.750 ± 0.433 | 0.890 ± 0.218 |
| 2.0x | 0.550 ± 0.497 | 0.650 ± 0.441 |
| 3.0x | 0.500 ± 0.500 | 0.533 ± 0.488 |
| 5.0x | 0.350 ± 0.477 | 0.383 ± 0.475 |

### Multi-Hop QA

| Target | Token F1 | ROUGE-L | Semantic similarity* | Key-fact recall |
|---:|---:|---:|---:|---:|
| 1.0x | 0.464 ± 0.089 | 0.391 ± 0.080 | 0.825 ± 0.054 | 0.531 ± 0.128 |
| 2.0x | 0.400 ± 0.091 | 0.328 ± 0.085 | 0.803 ± 0.070 | 0.413 ± 0.101 |
| 3.0x | 0.352 ± 0.085 | 0.285 ± 0.071 | 0.783 ± 0.083 | 0.360 ± 0.125 |
| 5.0x | 0.353 ± 0.080 | 0.280 ± 0.059 | 0.736 ± 0.087 | 0.334 ± 0.114 |

### Incident Summarization

| Target | ROUGE-L | ROUGE-1 | ROUGE-2 | Key-fact recall |
|---:|---:|---:|---:|---:|
| 1.0x | 0.319 ± 0.058 | 0.476 ± 0.050 | 0.172 ± 0.058 | 0.481 ± 0.081 |
| 2.0x | 0.267 ± 0.072 | 0.422 ± 0.070 | 0.114 ± 0.049 | 0.353 ± 0.100 |
| 3.0x | 0.261 ± 0.064 | 0.417 ± 0.072 | 0.100 ± 0.039 | 0.307 ± 0.076 |
| 5.0x | 0.232 ± 0.044 | 0.381 ± 0.072 | 0.069 ± 0.038 | 0.250 ± 0.070 |

*The original CSV does not record semantic-similarity backend provenance. The implementation supports a MiniLM embedding path and a token-Jaccard fallback; historical values cannot be attributed to MiniLM alone.*

## 5. Latency

| Task | Target | Compression ms | Inference ms | End-to-end ms | E2E vs baseline |
|---|---:|---:|---:|---:|---:|
| Extractive QA | 1x | 0.4 | 411.7 | 412.1 | 1.00x |
| Extractive QA | 2x | 3,985.4 | 337.0 | 4,322.4 | 10.49x |
| Extractive QA | 3x | 3,691.1 | 290.0 | 3,981.2 | 9.66x |
| Extractive QA | 5x | 3,839.9 | 254.9 | 4,094.8 | 9.94x |
| Multi-Hop QA | 1x | 0.4 | 1,970.7 | 1,971.1 | 1.00x |
| Multi-Hop QA | 2x | 5,220.5 | 1,649.7 | 6,870.2 | 3.49x |
| Multi-Hop QA | 3x | 3,863.2 | 1,729.5 | 5,592.7 | 2.84x |
| Multi-Hop QA | 5x | 4,920.3 | 1,309.4 | 6,229.7 | 3.16x |
| Summarization | 1x | 0.4 | 3,406.1 | 3,406.5 | 1.00x |
| Summarization | 2x | 5,529.0 | 2,161.5 | 7,690.5 | 2.26x |
| Summarization | 3x | 4,527.6 | 1,739.1 | 6,266.8 | 1.84x |
| Summarization | 5x | 5,466.9 | 1,410.7 | 6,877.6 | 2.02x |

Across all 60 cases, mean end-to-end latency was 1,929.9 ms at 1x and 5,734.0 ms at 5x (2.97x). Mean inference latency fell from 1,929.5 ms to 991.7 ms, but compression overhead dominated. The measured data do not identify whether compression ran on CPU or MPS, so the report does not attribute the overhead to a specific device.

## 6. Cost and Limitations

- Estimated input, output, and total cost fields are zero for all recorded runs. No commercial API cost reduction was measured.
- One run per case and ratio; no repeated-trial confidence intervals or significance tests.
- Semantic metric backend was not persisted in the original CSV.
- The dataset is synthetic and curated; it is not a production incident corpus.
- The CSV does not record the compressor execution device.
- Results are specific to the measured model, hardware, software, prompts, and dataset. Do not claim universal safe ratios.

## 7. Practical Interpretation

The experiment supports a tradeoff, not a universal deployment threshold: more compression reduces prompt length and inference latency but degrades several quality metrics and increases end-to-end latency in this local setup. Select ratios according to task risk and validate on a larger, externally sourced dataset with repeated trials before production deployment.
