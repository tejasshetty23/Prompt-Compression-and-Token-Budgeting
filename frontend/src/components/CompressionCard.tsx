import { useEffect, useState } from "react";
import type { AssistantMessage } from "../types";
import { fmt } from "../store";
import { Chevron, Compress } from "./Icons";

export function CompressionCard({ msg }: { msg: AssistantMessage }) {
  const [open, setOpen] = useState(false);
  const [slow, setSlow] = useState(false);
  const c = msg.compression;
  const pending = !c && msg.status === "compressing";

  useEffect(() => {
    if (!pending) return;
    const t = setTimeout(() => setSlow(true), 6000);
    return () => clearTimeout(t);
  }, [pending]);

  if (!c) {
    if (msg.status !== "compressing") return null;
    return (
      <div className="tool-card pending">
        <div className="tool-head static">
          <Compress size={15} />
          <span className="shimmer">
            {msg.targetRatio > 1 ? `Compressing context to ${msg.targetRatio}×…` : "Preparing prompt…"}
          </span>
          {slow && <span className="tool-dim">first run loads LLMLingua-2, ~1 min</span>}
        </div>
      </div>
    );
  }

  const t = c.telemetry;
  const m = c.compressor_metadata;
  const chunking = m.chunking;
  const kept = t.original_tokens ? Math.min(1, t.compressed_tokens / t.original_tokens) : 1;
  const noContext = t.original_tokens === 0;
  const method = m.method ?? "baseline";

  let summary: string;
  if (noContext) summary = "No context attached";
  else if (method === "baseline") summary = `Full context · ${fmt.int(t.original_tokens)} tokens`;
  else
    summary = `Compressed ${fmt.int(t.original_tokens)} → ${fmt.int(t.compressed_tokens)} tokens · ${fmt.ratio(
      t.compression_ratio,
    )}`;

  const budgetCut = msg.tokenBudget != null && method !== "baseline" && t.prompt_tokens >= msg.tokenBudget;

  return (
    <div className={"tool-card" + (open ? " open" : "")}>
      <button className="tool-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <Compress size={15} />
        <span className="tool-summary">{summary}</span>
        {!noContext && <span className="tool-dim">{fmt.ms(t.compression_latency_ms)}</span>}
        <Chevron size={15} className="tool-chevron" />
      </button>
      {open && (
        <div className="tool-body">
          {!noContext && (
            <div className="kept-bar" aria-label={`${Math.round(kept * 100)}% of context kept`}>
              <div className="kept-fill" style={{ width: `${kept * 100}%` }} />
              <span className="kept-label">
                {Math.round(kept * 100)}% kept · {fmt.pct((1 - kept) * 100)} saved
              </span>
            </div>
          )}
          <dl className="stat-grid">
            <Stat label="Original context" value={`${fmt.int(t.original_tokens)} tok`} />
            <Stat label="Compressed context" value={`${fmt.int(t.compressed_tokens)} tok`} />
            <Stat label="Full prompt" value={`${fmt.int(t.prompt_tokens)} tok`} />
            <Stat
              label="Ratio (actual / target)"
              value={`${fmt.ratio(t.compression_ratio)} / ${fmt.ratio(msg.targetRatio)}`}
            />
            <Stat label="Compression latency" value={fmt.ms(t.compression_latency_ms)} />
            <Stat label="Method" value={method} />
            {m.calibrated_rate_used != null && (
              <Stat label="Retention rate" value={m.calibrated_rate_used.toFixed(3)} />
            )}
            {m.refinements != null && method === "llmlingua" && (
              <Stat label="Feedback refinements" value={String(m.refinements)} />
            )}
            {chunking && (
              <Stat label="Chunks kept" value={`${chunking.chunks_selected} of ${chunking.chunks_created}`} />
            )}
            {msg.tokenBudget != null && (
              <Stat label="Token budget" value={`${fmt.int(msg.tokenBudget)}${budgetCut ? " (hit)" : ""}`} />
            )}
          </dl>
          {!noContext && (
            <>
              <div className="tool-sub">Context sent to the model</div>
              <pre className="context-pre">{c.context || "(empty after budget truncation)"}</pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
