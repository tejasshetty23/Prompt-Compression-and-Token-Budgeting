# Latency Trade-off Analysis

## 1. Purpose

This note separates the time spent compressing a prompt from the time spent generating an answer. Prompt compression can reduce the number of tokens sent to the language model while adding preprocessing overhead. The relevant outcome is therefore not compression time or inference time alone, but end-to-end latency.

## 2. Current repository benchmark snapshot

The repository README reports the following mean end-to-end latency across its benchmark tasks:

| Compression setting | Mean end-to-end latency |
|---|---:|
| 1x (baseline) | 1,929.9 ms |
| 5x | 5,734.0 ms |

The reported 5x end-to-end latency is approximately 2.97 times the 1x baseline. This snapshot does **not** demonstrate an end-to-end latency reduction at 5x.

The README also states that the benchmark records compression latency, inference latency, and end-to-end latency separately. Use the underlying CSV to populate the complete table below before making claims about inference-time changes.

## 3. Required decomposition

For each ratio and task, calculate:

`End_to_end_latency = Compression_latency + Inference_latency + Other_overhead`

Record the measured components separately. Do not infer inference latency from end-to-end latency.

| Target | Mean compression latency (ms) | Mean inference latency (ms) | Mean end-to-end latency (ms) | End-to-end change vs 1x (%) |
|---|---:|---:|---:|---:|
| 1x | TBD | TBD | 1,929.9 | 0.0 |
| 2x | TBD | TBD | TBD | TBD |
| 3x | TBD | TBD | TBD | TBD |
| 5x | TBD | TBD | 5,734.0 | TBD |

Calculate percentage change as:

`100 × (Latency_ratio - Latency_1x) / Latency_1x`

A negative value indicates a reduction; a positive value indicates an increase.

## 4. Recommended analysis

- Report mean and standard deviation for each latency component.
- Break results down by task type: extractive QA, multi-hop QA, and incident summarization.
- Keep model, hardware, warm-up policy, concurrency, and generation settings consistent.
- Run repeated trials if possible. The current README notes one run per case/ratio, not repeated trials.
- Report median and p95 latency if enough repeated observations are collected.
- Explain that local inference latency may not predict network/API latency in a hosted deployment.

## 5. Interpretation

A compression ratio can reduce inference time while still increasing end-to-end latency if compression takes longer than the inference time it saves. The current README's 1x and 5x snapshot demonstrates why both components must be reported.

Do not claim that compression improves total latency unless the measured end-to-end result supports that conclusion.

## 6. Status

**Status: partial evidence available in the repository README; full decomposition and repeated-trial analysis should be generated from benchmark data.**
