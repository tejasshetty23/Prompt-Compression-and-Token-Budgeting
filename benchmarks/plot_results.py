"""Generate research graphs: Accuracy, Latency, Cost, and Ratio Control.

Saves high-resolution figures to artifacts/figures/
"""
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Set publication style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "lines.linewidth": 2,
    "lines.markersize": 7,
})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="artifacts/benchmark_results.csv")
    parser.add_argument("--output-dir", default="artifacts/figures")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} runs for plotting from {args.input}")

    # Aggregate by task and target_ratio
    tasks = ["extractive_qa", "multi_hop_qa", "summarization"]
    ratios = sorted(df["target_ratio"].unique())

    # -------------------------------------------------------------------------
    # 1. ACCURACY VS COMPRESSION RATIO
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharex=True)

    # 1A. Extractive QA
    sub_ext = df[df["task"] == "extractive_qa"].groupby("target_ratio").mean(numeric_only=True)
    sub_ext_std = df[df["task"] == "extractive_qa"].groupby("target_ratio").std(numeric_only=True)
    ax = axes[0]
    ax.errorbar(sub_ext.index, sub_ext["exact_match"], yerr=sub_ext_std["exact_match"],
                fmt="-o", color="#1f77b4", capsize=4, label="Exact Match")
    ax.errorbar(sub_ext.index, sub_ext["f1"], yerr=sub_ext_std["f1"],
                fmt="--s", color="#aec7e8", capsize=4, label="Token F1")
    ax.set_title("Extractive QA")
    ax.set_xlabel("Target Compression Ratio")
    ax.set_ylabel("Score")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="lower left")
    ax.grid(True, linestyle="--", alpha=0.7)

    # 1B. Multi-Hop QA
    sub_multi = df[df["task"] == "multi_hop_qa"].groupby("target_ratio").mean(numeric_only=True)
    sub_multi_std = df[df["task"] == "multi_hop_qa"].groupby("target_ratio").std(numeric_only=True)
    ax = axes[1]
    ax.errorbar(sub_multi.index, sub_multi["f1"], yerr=sub_multi_std["f1"],
                fmt="-o", color="#ff7f0e", capsize=4, label="Token F1")
    if "semantic_similarity" in sub_multi.columns:
        ax.errorbar(sub_multi.index, sub_multi["semantic_similarity"], yerr=sub_multi_std["semantic_similarity"],
                    fmt="--^", color="#2ca02c", capsize=4, label="Semantic Similarity (backend not recorded)")
    if "key_fact_recall" in sub_multi.columns:
        ax.errorbar(sub_multi.index, sub_multi["key_fact_recall"], yerr=sub_multi_std["key_fact_recall"],
                    fmt=":d", color="#d62728", capsize=4, label="Key Fact Recall")
    ax.set_title("Multi-Hop QA")
    ax.set_xlabel("Target Compression Ratio")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="lower left")
    ax.grid(True, linestyle="--", alpha=0.7)

    # 1C. Summarization
    sub_sum = df[df["task"] == "summarization"].groupby("target_ratio").mean(numeric_only=True)
    sub_sum_std = df[df["task"] == "summarization"].groupby("target_ratio").std(numeric_only=True)
    ax = axes[2]
    ax.errorbar(sub_sum.index, sub_sum["rouge_l"], yerr=sub_sum_std["rouge_l"],
                fmt="-o", color="#9467bd", capsize=4, label="ROUGE-L")
    if "rouge_1" in sub_sum.columns:
        ax.errorbar(sub_sum.index, sub_sum["rouge_1"], yerr=sub_sum_std["rouge_1"],
                    fmt="--s", color="#8c564b", capsize=4, label="ROUGE-1")
    if "key_fact_recall" in sub_sum.columns:
        ax.errorbar(sub_sum.index, sub_sum["key_fact_recall"], yerr=sub_sum_std["key_fact_recall"],
                    fmt=":d", color="#e377c2", capsize=4, label="Fact Recall")
    ax.set_title("Incident Summarization")
    ax.set_xlabel("Target Compression Ratio")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="lower left")
    ax.grid(True, linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig(out_dir / "accuracy_vs_compression.png", dpi=300)
    plt.savefig(out_dir / "accuracy_vs_compression.pdf")
    plt.close()
    print("Saved accuracy_vs_compression.[png/pdf]")

    # -------------------------------------------------------------------------
    # 2. LATENCY BREAKDOWN (COMPRESSION VS INFERENCE VS TOTAL)
    # -------------------------------------------------------------------------
    lat_df = df.groupby("target_ratio").mean(numeric_only=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(lat_df.index))
    width = 0.28

    rects1 = ax.bar(x - width/2, lat_df["compression_latency_ms"], width, label="Compression Latency", color="#4575b4")
    rects2 = ax.bar(x + width/2, lat_df["inference_latency_ms"], width, label="Local LLM Inference Latency", color="#f46d43")

    ax.plot(x, lat_df["end_to_end_latency_ms"], color="#d73027", marker="o", linewidth=2.5, label="End-to-End Latency")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r}x" for r in lat_df.index])
    ax.set_xlabel("Target Compression Ratio")
    ax.set_ylabel("Latency (milliseconds)")
    ax.set_title("Latency Breakdown: Compression Overhead vs Local LLM Inference")
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig(out_dir / "latency_breakdown.png", dpi=300)
    plt.savefig(out_dir / "latency_breakdown.pdf")
    plt.close()
    print("Saved latency_breakdown.[png/pdf]")

    # -------------------------------------------------------------------------
    # 3. REQUESTED VS ACTUAL COMPRESSION RATIO CONTROL
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ratio_summary = df.groupby("target_ratio")["actual_compression_ratio"].agg(["mean", "std", "min", "max"]).reset_index()

    ax.plot([1.0, 5.0], [1.0, 5.0], "k--", alpha=0.6, label="Ideal 1:1 Target Line")
    ax.errorbar(ratio_summary["target_ratio"], ratio_summary["mean"],
                yerr=ratio_summary["std"], fmt="-o", color="#2b83ba", capsize=5,
                linewidth=2.5, markersize=8, label="Actual Measured (Mean ± Std)")

    # Highlight legacy overshoot for comparison
    legacy_targets = [1.0, 2.0, 3.0, 5.0]
    legacy_actuals = [1.0, 2.28, 3.60, 6.18]
    ax.plot(legacy_targets, legacy_actuals, ":^", color="#d7191c", alpha=0.7,
            linewidth=1.8, label="Uncalibrated Baseline (Overshoot)")

    ax.set_xlabel("Target Compression Ratio")
    ax.set_ylabel("Actual Measured Compression Ratio")
    ax.set_title("Compression Ratio Control: Calibrated Controller vs Baseline")
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig(out_dir / "ratio_control.png", dpi=300)
    plt.savefig(out_dir / "ratio_control.pdf")
    plt.close()
    print("Saved ratio_control.[png/pdf]")

    # -------------------------------------------------------------------------
    # 4. TOKEN REDUCTION & COST SAVINGS PROJECTION
    # -------------------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    tok_df = df.groupby("target_ratio").mean(numeric_only=True)

    color1 = "#2c7bb6"
    ax1.set_xlabel("Target Compression Ratio")
    ax1.set_ylabel("Mean Context Tokens Remaining", color=color1)
    ax1.plot(tok_df.index, tok_df["compressed_context_tokens"], color=color1, marker="o", linewidth=2.5)
    ax1.tick_params(axis="y", labelcolor=color1)

    ax2 = ax1.twinx()
    color2 = "#d7191c"
    # Project API cost savings at standard $3.00 / 1M tokens ($0.003 / 1k tokens) per 10,000 queries
    # Original prompt vs compressed prompt
    saved_tokens_per_req = tok_df["original_context_tokens"] - tok_df["compressed_context_tokens"]
    cost_saving_10k = (saved_tokens_per_req * 10000 / 1_000_000) * 3.00 # $3/Mtok
    ax2.set_ylabel("Estimated Cost Savings per 10k Requests (USD)", color=color2)
    ax2.plot(tok_df.index, cost_saving_10k, color=color2, marker="s", linestyle="--", linewidth=2.5)
    ax2.tick_params(axis="y", labelcolor=color2)

    plt.title("Token Reduction and Projected API Cost Savings ($3/M tokens)")
    plt.tight_layout()
    plt.savefig(out_dir / "cost_token_savings.png", dpi=300)
    plt.savefig(out_dir / "cost_token_savings.pdf")
    plt.close()
    print("Saved cost_token_savings.[png/pdf]")

if __name__ == "__main__":
    main()
