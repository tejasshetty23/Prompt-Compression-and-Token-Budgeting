"""Run model-backed compression benchmarks with excluded model warm-up calls."""
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
    parser.add_argument(
        "--warmup-runs", type=int, default=2,
        help="Unmeasured local-model warm-up calls before benchmark runs (default: 2).",
    )
    args = parser.parse_args()

    if args.warmup_runs < 0:
        parser.error("--warmup-runs cannot be negative")

    config = load_config(args.config)
    client = ChatCompletionClient(model=args.model)
    middleware = PromptBudgetMiddleware(config)
    rows = []
    cases = [
        json.loads(line)
        for line in Path(args.input).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not cases:
        raise ValueError("Benchmark input contains no cases")

    for case in cases:
        required = {"question", "context", "reference", "task"}
        missing = required - case.keys()
        if missing:
            raise ValueError(f"Benchmark case missing required fields: {sorted(missing)}")

    # Warm the compressor and downstream model once; exclude this call from results.
    warmup_case = cases[0]
    warmup_prepared = middleware.prepare(
        warmup_case.get("system_instruction", ""),
        warmup_case["question"],
        warmup_case["context"],
        target_ratio=max(config.benchmark.ratios),
        task=warmup_case["task"],
    )
    client.answer(
        warmup_prepared.system_instruction,
        warmup_prepared.question,
        warmup_prepared.context,
        temperature=0,
    )
    print("Completed excluded compressor + LLM warm-up")

    # Additional downstream-model warm-ups are also excluded from the CSV.
    for warmup_index in range(args.warmup_runs):
        client.answer(
            "Answer briefly.", "What is 2 + 2?", "The answer is 4.", temperature=0,
        )
        print(f"Completed excluded LLM warm-up {warmup_index + 1}/{args.warmup_runs}")

    total_runs = len(cases) * len(config.benchmark.ratios) * config.benchmark.runs_per_case
    completed_runs = 0

    for case_index, case in enumerate(cases, start=1):
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

                # Exact match is most interpretable for short extractive answers.
                # Multi-hop answers are explanatory, so report token F1 and ROUGE-L.
                quality = {}
                if task == "extractive_qa":
                    quality["exact_match"] = exact_match(prediction, reference)
                    quality["f1"] = token_f1(prediction, reference)
                elif task == "multi_hop_qa":
                    quality["f1"] = token_f1(prediction, reference)
                    quality["rouge_l"] = rouge_l(prediction, reference)
                elif task == "summarization":
                    quality["rouge_l"] = rouge_l(prediction, reference)
                else:
                    raise ValueError(f"Unsupported benchmark task: {task}")

                input_tokens = inference["prompt_tokens"]
                output_tokens = inference["completion_tokens"]
                if input_tokens is None:
                    input_tokens = count_tokens(prepared.prompt, config.tokenizer.encoding_name)
                if output_tokens is None:
                    output_tokens = count_tokens(prediction, config.tokenizer.encoding_name)
                input_cost = input_tokens / 1000 * config.cost.input_usd_per_1k_tokens
                output_cost = output_tokens / 1000 * config.cost.output_usd_per_1k_tokens
                original_context_tokens = count_tokens(case["context"], config.tokenizer.encoding_name)
                compressed_context_tokens = count_tokens(prepared.context, config.tokenizer.encoding_name)

                rows.append({
                    "case_id": case.get("id"),
                    "task": task,
                    "target_ratio": ratio,
                    "actual_compression_ratio": round(
                        original_context_tokens / max(1, compressed_context_tokens), 4
                    ),
                    "context_token_reduction_pct": round(
                        (1 - compressed_context_tokens / max(1, original_context_tokens)) * 100, 4
                    ),
                    "run": run_index + 1,
                    "model": inference["model"],
                    "original_context_tokens": original_context_tokens,
                    "compressed_context_tokens": compressed_context_tokens,
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "actual_api_total_tokens": inference["total_tokens"],
                    "compression_latency_ms": prepared.telemetry.compression_latency_ms,
                    "inference_latency_ms": inference["latency_ms"],
                    "end_to_end_latency_ms": (
                        prepared.telemetry.compression_latency_ms + inference["latency_ms"]
                    ),
                    "estimated_input_cost_usd": input_cost,
                    "estimated_output_cost_usd": output_cost,
                    "estimated_total_cost_usd": input_cost + output_cost,
                    "prediction": prediction,
                    "reference": reference,
                    **quality,
                })
                completed_runs += 1
                print(
                    f"[{completed_runs}/{total_runs}] case {case_index}/{len(cases)} "
                    f"{case.get('id', 'unnamed')} | target {ratio}x | "
                    f"run {run_index + 1}/{config.benchmark.runs_per_case} | "
                    f"inference {inference['latency_ms']:.0f} ms",
                    flush=True,
                )

                # Periodically checkpoint results so an interrupted run loses little work.
                if completed_runs % 12 == 0:
                    checkpoint = Path(args.output)
                    checkpoint.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(rows).to_csv(checkpoint, index=False)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)
    print(f"Wrote {len(rows)} measured runs to {output}")
    print(f"Excluded warm-up calls: {args.warmup_runs + 1} (1 compressor + LLM, {args.warmup_runs} additional LLM)")


if __name__ == "__main__":
    main()
