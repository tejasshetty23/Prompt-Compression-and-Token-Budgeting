"""Summarize measured benchmark runs by task and target compression ratio.

Actual compression is derived from original_context_tokens / compressed_context_tokens.
This script reports descriptive statistics; it does not declare a safe ratio.
"""
import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="artifacts/benchmark_results.csv")
    parser.add_argument("--output", default="artifacts/benchmark_summary.csv")
    args = parser.parse_args()

    source = Path(args.input)
    if not source.exists():
        raise FileNotFoundError(f"Results file not found: {source}")

    df = pd.read_csv(source)
    required = {
        "task", "target_ratio", "original_context_tokens",
        "compressed_context_tokens", "compression_latency_ms",
        "inference_latency_ms", "end_to_end_latency_ms",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Results CSV is missing columns: {sorted(missing)}")

    df["actual_compression_ratio"] = (
        df["original_context_tokens"]
        / df["compressed_context_tokens"].clip(lower=1)
    )
    df["context_token_reduction_pct"] = (
        1 - df["compressed_context_tokens"]
        / df["original_context_tokens"].clip(lower=1)
    ) * 100

    quality_columns = [
        col for col in ("exact_match", "f1", "rouge_l")
        if col in df.columns
    ]
    measure_columns = [
        "actual_compression_ratio",
        "context_token_reduction_pct",
        "original_context_tokens",
        "compressed_context_tokens",
        "prompt_tokens",
        "compression_latency_ms",
        "inference_latency_ms",
        "end_to_end_latency_ms",
        "estimated_total_cost_usd",
        *quality_columns,
    ]
    measure_columns = [c for c in measure_columns if c in df.columns]

    grouped = df.groupby(["task", "target_ratio"], dropna=False)[measure_columns]
    summary = grouped.agg(["mean", "std"]).reset_index()
    summary.columns = [
        "_".join(str(part) for part in col if str(part))
        if isinstance(col, tuple) else str(col)
        for col in summary.columns
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output, index=False)

    print(f"Loaded {len(df)} measured runs across {df['task'].nunique()} tasks.")
    print(f"Cases: {df['case_id'].nunique() if 'case_id' in df else 'unknown'}")
    print(f"Summary saved to: {output}")
    print("\nMean results by task and target ratio:")
    display_columns = ["task", "target_ratio"]
    for col in (
        "actual_compression_ratio", "context_token_reduction_pct",
        "end_to_end_latency_ms", "exact_match", "f1", "rouge_l",
    ):
        mean_col = f"{col}_mean"
        if mean_col in summary.columns:
            display_columns.append(mean_col)
    print(summary[display_columns].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
