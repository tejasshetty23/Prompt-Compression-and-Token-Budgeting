import { useEffect, type ReactNode } from "react";
import type { Attachment, GlobalSettings, Health } from "../types";
import { DEFAULT_SYSTEM, fmt } from "../store";
import { X } from "./Icons";

function Modal({ title, onClose, children, wide }: { title: string; onClose: () => void; children: ReactNode; wide?: boolean }) {
  useEffect(() => {
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
  }, [onClose]);
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={"modal" + (wide ? " wide" : "")} role="dialog" aria-modal aria-label={title}>
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <X />
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

export function AttachmentDialog({ attachment, onClose }: { attachment: Attachment; onClose: () => void }) {
  const LIMIT = 40_000;
  return (
    <Modal title={attachment.name} onClose={onClose} wide>
      <div className="modal-meta">
        {fmt.int(attachment.tokens)} tokens · {fmt.int(attachment.text.length)} characters
      </div>
      <pre className="context-pre tall">
        {attachment.text.slice(0, LIMIT)}
        {attachment.text.length > LIMIT && "\n\n… (preview truncated)"}
      </pre>
    </Modal>
  );
}

export function SettingsDialog({
  settings,
  health,
  healthError,
  onChange,
  onClearAll,
  onClose,
}: {
  settings: GlobalSettings;
  health: Health | null;
  healthError: string | null;
  onChange: (s: Partial<GlobalSettings>) => void;
  onClearAll: () => void;
  onClose: () => void;
}) {
  return (
    <Modal title="Settings" onClose={onClose}>
      <section className="field">
        <label htmlFor="sys">System instruction</label>
        <p className="field-hint">Kept verbatim in every prompt. Only the attached context is compressed.</p>
        <textarea
          id="sys"
          className="text-input"
          rows={4}
          value={settings.systemInstruction}
          onChange={(e) => onChange({ systemInstruction: e.target.value })}
        />
        {settings.systemInstruction !== DEFAULT_SYSTEM && (
          <button className="link-btn" onClick={() => onChange({ systemInstruction: DEFAULT_SYSTEM })}>
            Reset to default
          </button>
        )}
      </section>

      <section className="field">
        <label htmlFor="temp">Temperature · {settings.temperature.toFixed(1)}</label>
        <input
          id="temp"
          type="range"
          min={0}
          max={1.5}
          step={0.1}
          value={settings.temperature}
          onChange={(e) => onChange({ temperature: parseFloat(e.target.value) })}
        />
      </section>

      <section className="field">
        <label>Appearance</label>
        <div className="segmented">
          {(["system", "light", "dark"] as const).map((t) => (
            <button key={t} className={settings.theme === t ? "on" : ""} onClick={() => onChange({ theme: t })}>
              {t[0].toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </section>

      <section className="field">
        <label>Backend</label>
        {healthError ? (
          <p className="field-hint bad-text">
            Can't reach the API ({healthError}). Start it from the repo root with{" "}
            <code>uvicorn prompt_budget.api:app --reload</code>.
          </p>
        ) : health ? (
          <dl className="kv">
            <dt>LLM endpoint</dt>
            <dd>{health.llm.base_url}</dd>
            <dt>Status</dt>
            <dd>{health.llm.reachable ? `${health.llm.models.length} model(s) available` : health.llm.error}</dd>
            <dt>Compressor</dt>
            <dd>{health.compressor.model_name}</dd>
            <dt>Chunking</dt>
            <dd>
              {health.config.chunk_size_tokens} tok / {health.config.chunk_overlap_tokens} overlap · top{" "}
              {health.config.top_k_chunks}
            </dd>
            <dt>Ratio control</dt>
            <dd>
              {health.config.adaptive_control ? `adaptive, τ = ${health.config.tolerance}` : "open loop (1/R)"}
            </dd>
          </dl>
        ) : (
          <p className="field-hint">Checking…</p>
        )}
      </section>

      <section className="field">
        <button
          className="danger-btn"
          onClick={() => {
            if (confirm("Delete all chats? This can't be undone.")) onClearAll();
          }}
        >
          Delete all chats
        </button>
      </section>
    </Modal>
  );
}
