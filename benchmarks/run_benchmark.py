"""Run real model-backed benchmark experiments across configured compression ratios."""
import argparse
import json
from pathlib import Path
import pandas as pd

from prompt_budget.config import load_config
from prompt_budget.middleware import PromptBudgetMiddleware
from prompt_budget.llm_client import ChatCompletionClient
from prompt_budget.tokenization import count_tokens
from metrics import exact_match, token_f1, rouge_l

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/benchmark.example.jsonl")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--output", default="artifacts/benchmark_results.csv")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    client = ChatCompletionClient(model=args.model)
    middleware = PromptBudgetMiddleware(config)
    rows = []

    for line in Path(args.input).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        required = {"question", "context", "reference", "task"}
        missing = required - case.keys()
        if missing:
            raise ValueError(f"Benchmark case missing required fields: {sorted(missing)}")

        for ratio in config.benchmark.ratios:
            for run_index in range(config.benchmark.runs_per_case):
                prepared = middleware.prepare(
                    case.get("system_instruction", ""),
                    case["question"],
                    case["context"],
                    target_ratio=ratio,
                    task=case["task"],
                )
                inference = client.answer(
                    prepared.system_instruction,
                    prepared.question,
                    prepared.context,
                    temperature=config.benchmark.temperature,
                )
                prediction, reference = inference["answer"], case["reference"]
                task = case["task"]
                quality = (
                    {"exact_match": exact_match(prediction, reference),
                     "f1": token_f1(prediction, reference)}
                    if task in {"extractive_qa", "multi_hop_qa"}
                    else {"rouge_l": rouge_l(prediction, reference)}
                )
                input_tokens = inference["prompt_tokens"]
                output_tokens = inference["completion_tokens"]
                if input_tokens is None:
                    input_tokens = count_tokens(prepared.prompt, config.tokenizer.encoding_name)
                if output_tokens is None:
                    output_tokens = count_tokens(prediction, config.tokenizer.encoding_name)
                input_cost = input_tokens / 1000 * config.cost.input_usd_per_1k_tokens
                output_cost = output_tokens / 1000 * config.cost.output_usd_per_1k_tokens
                rows.append({
                    "case_id": case.get("id"),
                    "task": task,
                    "target_ratio": ratio,
                    "run": run_index + 1,
                    "model": inference["model"],
                    "original_context_tokens": count_tokens(case["context"], config.tokenizer.encoding_name),
                    "compressed_context_tokens": count_tokens(prepared.context, config.tokenizer.encoding_name),
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "actual_api_total_tokens": inference["total_tokens"],
                    "compression_latency_ms": prepared.telemetry.compression_latency_ms,
                    "inference_latency_ms": inference["latency_ms"],
                    "end_to_end_latency_ms": prepared.telemetry.compression_latency_ms + inference["latency_ms"],
                    "estimated_input_cost_usd": input_cost,
                    "estimated_output_cost_usd": output_cost,
                    "estimated_total_cost_usd": input_cost + output_cost,
                    "prediction": prediction,
                    "reference": reference,
                    **quality,
                })

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)
    print(f"Wrote {len(rows)} measured runs to {output}")

if __name__ == "__main__":
    main()
