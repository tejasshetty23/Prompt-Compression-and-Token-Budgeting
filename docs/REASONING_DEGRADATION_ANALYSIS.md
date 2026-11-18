# Reasoning Quality and Compression-Degradation Analysis

## 1. Objective

The project guidelines ask the benchmark to identify the compression threshold at which reasoning capacity begins to degrade. This requires comparing answer quality at each compression level against an uncompressed baseline, not merely reporting the achieved compression ratio.

## 2. Evaluation tasks and metrics

The repository describes a 60-case synthetic benchmark with 20 cases in each task:

- Extractive question answering
- Multi-hop question answering
- Incident summarization

The README lists task-appropriate metrics including Exact Match, Token F1, ROUGE-1/2/L, Key Fact Recall, and semantic similarity. Use the metric appropriate to each task and explain its interpretation.

## 3. Analysis procedure

1. Treat 1x as the uncompressed reference condition.
2. For every case, compare the answer at 2x, 3x, and 5x with that case's 1x answer and reference answer.
3. Aggregate results by task and compression target.
4. Report mean and standard deviation; retain per-case results to expose failures hidden by averages.
5. Define a degradation criterion before interpreting results. A defensible project-level criterion is a decline greater than a pre-declared tolerance relative to the 1x baseline. State the tolerance and justify it; do not select it after seeing the results.
6. Identify the first tested ratio that crosses the criterion. Since only discrete ratios are tested, describe this as the first *observed tested level*, not an exact continuous threshold.

## 4. Results table to complete

| Task | Metric | 1x baseline | 2x | 3x | 5x | First tested level crossing degradation criterion |
|---|---|---:|---:|---:|---:|---|
| Extractive QA | Exact Match / Token F1 | TBD | TBD | TBD | TBD | TBD |
| Multi-hop QA | Token F1 / Key Fact Recall | TBD | TBD | TBD | TBD | TBD |
| Incident summarization | ROUGE / Key Fact Recall | TBD | TBD | TBD | TBD | TBD |

Do not fill these cells with invented values. Generate them from the committed benchmark results and metric outputs.

## 5. Recommended figures

- Task metric versus actual compression ratio (one line per task).
- Key Fact Recall versus actual compression ratio.
- Per-case quality change from 1x to each compressed setting.
- Actual achieved compression ratio versus requested target.

Use *actual achieved compression ratio* on the x-axis where available. The repository README reports aggregate actual ratios of 1.000, 1.980, 2.984, and 4.837 for the 1x, 2x, 3x, and 5x settings respectively.

## 6. Important interpretation cautions

- Do not assume that a requested 5x target means every prompt achieved 5x. The README reports that 27 of 60 cases were within ±5% of the 5x target.
- The README notes that the semantic-similarity CSV does not preserve whether MiniLM or a token-Jaccard fallback was used. Explain this limitation when interpreting that metric.
- A quality decline is not automatically proof of lost general reasoning ability; it is evidence of degradation on this benchmark and its task distribution.
- The dataset is synthetic and curated, so generalisation to production telemetry is not established.

## 7. Status

**Status: analysis protocol; the degradation threshold must be calculated from the actual per-case benchmark results before a conclusion is stated.**
