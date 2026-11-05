"""Evaluate precomputed model predictions for each compression ratio."""
import argparse
import json
from pathlib import Path
import pandas as pd
from prompt_budget.config import load_config
from prompt_budget.middleware import PromptBudgetMiddleware
from prompt_budget.tokenization import count_tokens
from metrics import exact_match, token_f1, rouge_l

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/benchmark.example.jsonl")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--output", default="artifacts/benchmark_results.csv")
    args = parser.parse_args()
    config = load_config(args.config)
    middleware = PromptBudgetMiddleware(config)
    rows = []
    for line in Path(args.input).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        for ratio in config.benchmark.ratios:
            result = middleware.prepare(case.get("system_instruction", ""), case["question"],
                case["context"], target_ratio=ratio, task=case["task"])
            prediction = case.get("prediction_by_ratio", {}).get(str(ratio), "")
            reference, task = case.get("reference", ""), case["task"]
            quality = ({"exact_match": exact_match(prediction, reference),
                        "f1": token_f1(prediction, reference)} if task != "summarization"
                       else {"rouge_l": rouge_l(prediction, reference)})
            rows.append({"case_id": case.get("id"), "task": task, "target_ratio": ratio,
                "original_context_tokens": count_tokens(case["context"], config.tokenizer.encoding_name),
                "compressed_context_tokens": count_tokens(result.context, config.tokenizer.encoding_name),
                "prompt_tokens": result.telemetry.prompt_tokens,
                "compression_latency_ms": result.telemetry.compression_latency_ms, **quality})
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(f"Wrote {len(rows)} rows to {args.output}")

if __name__ == "__main__":
    main()
