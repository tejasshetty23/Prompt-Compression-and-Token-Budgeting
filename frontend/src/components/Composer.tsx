import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { Attachment, ConvSettings, Task } from "../types";
import { TASK_LABELS, fmt } from "../store";
import { ArrowUp, ChevronDown, FileIcon, Paperclip, Sliders, Stop, X } from "./Icons";

const PASTE_AS_ATTACHMENT_CHARS = 1500;
const RATIOS = [1, 2, 3, 5];
const ACCEPT = ".pdf,.txt,.log,.md,.csv,.json,.jsonl";

type Props = {
  busy: boolean;
  attachments: Attachment[];
  uploading: string[];
  settings: ConvSettings;
  models: string[];
  model: string | null;
  connecting?: boolean;
  autoFocus?: boolean;
  placeholder?: string;
  onSend: (text: string) => void;
  onStop: () => void;
  onAddFiles: (files: File[]) => void;
  onAddPaste: (text: string) => void;
  onRemoveAttachment: (id: string) => void;
  onPreviewAttachment: (a: Attachment) => void;
  onSettingsChange: (s: Partial<ConvSettings>) => void;
  onModelChange: (m: string) => void;
};

function usePopover() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);
  return { open, setOpen, ref };
}

export function Composer(props: Props) {
  const { busy, attachments, uploading, settings, models, model } = props;
  const [text, setText] = useState("");
  const taRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const tune = usePopover();
  const modelMenu = usePopover();

  useLayoutEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "0px";
    ta.style.height = Math.min(ta.scrollHeight, 280) + "px";
  }, [text]);

  useEffect(() => {
    if (props.autoFocus) taRef.current?.focus();
  }, [props.autoFocus]);

  const canSend = text.trim().length > 0 && !busy;
  const contextTokens = attachments.reduce((n, a) => n + a.tokens, 0);

  const submit = () => {
    if (!canSend) return;
    props.onSend(text.trim());
    setText("");
  };

  const ratioLabel = settings.targetRatio === 1 ? "No compression" : `${settings.targetRatio}× compression`;

  return (
    <div className="composer">
      {(attachments.length > 0 || uploading.length > 0) && (
        <div className="attachments">
          {attachments.map((a) => (
            <div key={a.id} className="attachment" title={a.name}>
              <button className="attachment-body" onClick={() => props.onPreviewAttachment(a)}>
                <span className="attachment-icon"><FileIcon size={16} /></span>
                <span className="attachment-text">
                  <span className="attachment-name">{a.name}</span>
                  <span className="attachment-meta">{fmt.int(a.tokens)} tokens</span>
                </span>
              </button>
              <button
                className="attachment-remove"
                aria-label={`Remove ${a.name}`}
                onClick={() => props.onRemoveAttachment(a.id)}
              >
                <X size={12} />
              </button>
            </div>
          ))}
          {uploading.map((name) => (
            <div key={name} className="attachment uploading">
              <span className="attachment-body">
                <span className="attachment-icon spinner" />
                <span className="attachment-text">
                  <span className="attachment-name">{name}</span>
                  <span className="attachment-meta">Reading…</span>
                </span>
              </span>
            </div>
          ))}
        </div>
      )}

      <textarea
        ref={taRef}
        className="composer-input"
        rows={1}
        value={text}
        placeholder={props.placeholder ?? "Ask a question about your context…"}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            submit();
          }
        }}
        onPaste={(e) => {
          const pasted = e.clipboardData.getData("text");
          if (pasted.length >= PASTE_AS_ATTACHMENT_CHARS) {
            e.preventDefault();
            props.onAddPaste(pasted);
          }
        }}
      />

      <div className="composer-bar">
        <div className="composer-tools">
          <input
            ref={fileRef}
            type="file"
            accept={ACCEPT}
            multiple
            hidden
            onChange={(e) => {
              const files = Array.from(e.target.files ?? []);
              if (files.length) props.onAddFiles(files);
              e.target.value = "";
            }}
          />
          <button
            className="icon-btn outlined"
            title="Attach context (PDF, log, txt, md, csv, json)"
            aria-label="Attach context"
            onClick={() => fileRef.current?.click()}
          >
            <Paperclip size={17} />
          </button>

          <div className="popover-anchor" ref={tune.ref}>
            <button
              className={"chip-btn" + (tune.open ? " active" : "")}
              onClick={() => tune.setOpen(!tune.open)}
              aria-expanded={tune.open}
            >
              <Sliders size={16} />
              <span>{ratioLabel}</span>
              {settings.tokenBudget != null && <span className="chip-sub">· {fmt.int(settings.tokenBudget)} max</span>}
            </button>
            {tune.open && (
              <div className="popover up">
                <div className="popover-section">
                  <div className="popover-label">Target ratio</div>
                  <div className="segmented">
                    {RATIOS.map((r) => (
                      <button
                        key={r}
                        className={settings.targetRatio === r ? "on" : ""}
                        onClick={() => props.onSettingsChange({ targetRatio: r })}
                      >
                        {r}×
                      </button>
                    ))}
                    <input
                      type="number"
                      min={1}
                      step={0.5}
                      aria-label="Custom ratio"
                      value={RATIOS.includes(settings.targetRatio) ? "" : settings.targetRatio}
                      placeholder="Custom"
                      onChange={(e) => {
                        const v = parseFloat(e.target.value);
                        if (v >= 1) props.onSettingsChange({ targetRatio: v });
                      }}
                    />
                  </div>
                  <p className="popover-hint">
                    LLMLingua-2 keeps roughly 1/R of the context. The instruction and question are never compressed.
                  </p>
                </div>
                <div className="popover-section">
                  <label className="popover-label row">
                    <span>Token budget</span>
                    <input
                      type="checkbox"
                      className="switch"
                      checked={settings.tokenBudget != null}
                      onChange={(e) => props.onSettingsChange({ tokenBudget: e.target.checked ? 1000 : null })}
                    />
                  </label>
                  {settings.tokenBudget != null && (
                    <input
                      type="number"
                      className="text-input"
                      min={1}
                      value={settings.tokenBudget}
                      onChange={(e) => {
                        const v = parseInt(e.target.value, 10);
                        props.onSettingsChange({ tokenBudget: Number.isFinite(v) && v > 0 ? v : 1 });
                      }}
                    />
                  )}
                  <p className="popover-hint">Hard cap on the whole prompt. Context is truncated to fit.</p>
                </div>
                <div className="popover-section">
                  <div className="popover-label">Task</div>
                  <select
                    className="text-input"
                    value={settings.task}
                    onChange={(e) => props.onSettingsChange({ task: e.target.value as Task })}
                  >
                    {Object.entries(TASK_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="composer-right">
          {contextTokens > 0 && (
            <span className="context-count" title="Context tokens before compression">
              {fmt.int(contextTokens)} tokens
            </span>
          )}
          <div className="popover-anchor" ref={modelMenu.ref}>
            <button className="model-btn" onClick={() => modelMenu.setOpen(!modelMenu.open)} aria-expanded={modelMenu.open}>
              <span>{model ?? (props.connecting ? "Connecting…" : "No model")}</span>
              <ChevronDown size={14} />
            </button>
            {modelMenu.open && (
              <div className="popover up right menu">
                {models.length === 0 && <div className="menu-empty">No models found. Is Ollama running?</div>}
                {models.map((m) => (
                  <button
                    key={m}
                    className={"menu-item" + (m === model ? " on" : "")}
                    onClick={() => {
                      props.onModelChange(m);
                      modelMenu.setOpen(false);
                    }}
                  >
                    {m}
                  </button>
                ))}
              </div>
            )}
          </div>
          {busy ? (
            <button className="send-btn" onClick={props.onStop} aria-label="Stop generating">
              <Stop size={16} />
            </button>
          ) : (
            <button className="send-btn" onClick={submit} disabled={!canSend} aria-label="Send">
              <ArrowUp size={17} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
