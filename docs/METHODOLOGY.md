# Benchmark methodology

## Experimental design
Evaluate the uncompressed baseline (1x) and target compression ratios 2x, 3x, and 5x. Keep the downstream model, prompt template, decoding settings (temperature 0), dataset split, and chunking configuration fixed across ratios. Run each experiment cell three times and report mean and standard deviation.

## Tasks and metrics
- Extractive QA and multi-hop QA: Exact Match and token-level F1.
- Summarization: ROUGE-L and a separately documented LLM-as-a-judge rubric.
- System: original, compressed, and total prompt token counts; compression latency; end-to-end latency; estimated input cost per request and per 1,000 requests.

## Confounds
Compressor model choice and chunk boundaries independently affect quality. Record both in each experiment. Do not compare ratios across runs that change either setting.

## Degradation threshold
For each task, define the maximum safe ratio as the highest tested ratio whose quality decrease from the 1x baseline remains within a predeclared tolerance. Report the tolerance and sample size. Do not infer a threshold from example data.

## Limitation of the included runner
The runner computes metrics for predictions supplied in the JSONL input. A downstream model adapter must generate predictions for each compressed prompt before answer-quality results are meaningful. The example JSONL is an interface example, not an empirical result.
