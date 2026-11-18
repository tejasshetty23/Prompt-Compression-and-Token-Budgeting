import { useEffect, useState } from "react";
import { api } from "../api";
import type { SummaryRow } from "../types";
import { TASK_LABELS, fmt } from "../store";

type Col = { key: string; label: string; format: (v: number | null) => string };

const num = (d: number) => (v: number | null) => (v == null ? "—" : v.toFixed(d));

const COMMON: Col[] = [
  { key: "target_ratio", label: "Target", format: (v) => (v == null ? "—" : `${v}×`) },
  { key: "actual_compression_ratio_mean", label: "Actual ratio", format: (v) => fmt.ratio(v) },
  { key: "context_token_reduction_pct_mean", label: "Tokens saved", format: (v) => fmt.pct(v) },
  { key: "compression_latency_ms_mean", label: "Compression", format: (v) => fmt.ms(v) },
  { key: "end_to_end_latency_ms_mean", label: "End-to-end", format: (v) => fmt.ms(v) },
];

const QUALITY: Record<string, Col[]> = {
  extractive_qa: [
    { key: "exact_match_mean", label: "Exact match", format: num(2) },
    { key: "f1_mean", label: "Token F1", format: num(2) },
  ],
  multi_hop_qa: [
    { key: "exact_match_mean", label: "Exact match", format: num(2) },
    { key: "f1_mean", label: "Token F1", format: num(2) },
  ],
  summarization: [
    { key: "rouge_l_mean", label: "ROUGE-L", format: num(2) },
    { key: "key_fact_recall_mean", label: "Key-fact recall", format: num(2) },
    { key: "semantic_similarity_mean", label: "Semantic sim.", format: num(2) },
  ],
};

const FIGURE_TITLES: Record<string, string> = {
  "accuracy_vs_compression.png": "Task quality vs. compression ratio",
  "cost_token_savings.png": "Token savings",
  "latency_breakdown.png": "Latency breakdown",
  "ratio_control.png": "Ratio control: target vs. actual",
};

export function BenchmarksView() {
  const [data, setData] = useState<{ summary: SummaryRow[]; figures: string[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [task, setTask] = useState("extractive_qa");

  useEffect(() => {
    api.benchmarks().then(setData).catch((e) => setError(String(e.message ?? e)));
  }, []);

  const tasks = data ? [...new Set(data.summary.map((r) => String(r.task)))] : [];
  const rows = data?.summary.filter((r) => r.task === task) ?? [];
  const cols = [...COMMON, ...(QUALITY[task] ?? [])];

  return (
    <div className="page">
      <div className="page-inner">
        <header className="page-head">
          <h1>Benchmark results</h1>
          <p>
            60 synthetic incident cases (20 per task) run at 1×, 2×, 3× and 5× with LLMLingua-2 and{" "}
            <code>qwen2.5:1.5b</code> via Ollama. One run per case and ratio; values are means.
          </p>
        </header>

        {error && <div className="error-card"><div><strong>Couldn't load results</strong><p>{error}</p></div></div>}
        {!data && !error && <div className="shimmer">Loading…</div>}

        {data && (
          <>
            <div className="tabs" role="tablist">
              {tasks.map((t) => (
                <button key={t} role="tab" aria-selected={t === task} className={t === task ? "on" : ""} onClick={() => setTask(t)}>
                  {TASK_LABELS[t] ?? t}
                </button>
              ))}
            </div>

            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>{cols.map((c) => <th key={c.key}>{c.label}</th>)}</tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={String(r.target_ratio)}>
                      {cols.map((c) => (
                        <td key={c.key}>{c.format(typeof r[c.key] === "number" ? (r[c.key] as number) : null)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {data.figures.length > 0 && (
              <>
                <h2 className="section-title">Figures</h2>
                <div className="figure-grid">
                  {data.figures.map((src) => {
                    const name = src.split("/").pop() ?? src;
                    return (
                      <a key={src} className="figure" href={src} target="_blank" rel="noreferrer">
                        <img src={src} alt={FIGURE_TITLES[name] ?? name} loading="lazy" />
                        <span>{FIGURE_TITLES[name] ?? name}</span>
                      </a>
                    );
                  })}
                </div>
              </>
            )}
            <p className="footnote">
              The dataset is synthetic and curated, not production telemetry. Local inference cost is configured as zero, so
              commercial API savings were not measured.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
