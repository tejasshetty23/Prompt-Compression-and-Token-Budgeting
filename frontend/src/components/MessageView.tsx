import { memo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { AssistantMessage, Message } from "../types";
import { fmt } from "../store";
import { CompressionCard } from "./CompressionCard";
import { Alert, Check, Copy, Mark, Retry } from "./Icons";

const Markdown = memo(({ text }: { text: string }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
));

export function MessageView({
  msg,
  isLast,
  onRetry,
}: {
  msg: Message;
  isLast: boolean;
  onRetry: () => void;
}) {
  if (msg.role === "user") {
    return (
      <div className="msg-user">
        <div className="bubble">{msg.content}</div>
      </div>
    );
  }
  return <AssistantView msg={msg} isLast={isLast} onRetry={onRetry} />;
}

function AssistantView({ msg, isLast, onRetry }: { msg: AssistantMessage; isLast: boolean; onRetry: () => void }) {
  const [copied, setCopied] = useState(false);
  const streaming = msg.status === "generating" || msg.status === "compressing";

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(msg.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked */
    }
  };

  return (
    <div className="msg-assistant">
      <CompressionCard msg={msg} />

      {msg.content && (
        <div className={"prose" + (msg.status === "generating" ? " streaming" : "")}>
          <Markdown text={msg.content} />
        </div>
      )}

      {msg.status === "generating" && !msg.content && (
        <div className="thinking">
          <Mark size={18} className="pulse" />
        </div>
      )}

      {msg.status === "error" && (
        <div className="error-card">
          <Alert size={16} />
          <div>
            <strong>{msg.compression ? "The model didn't respond" : "Compression failed"}</strong>
            <p>{msg.error}</p>
          </div>
        </div>
      )}

      {msg.status === "stopped" && <div className="stopped-note">Stopped.</div>}

      {!streaming && (
        <div className={"msg-actions" + (isLast ? " visible" : "")}>
          {msg.content && (
            <button className="icon-btn sm" onClick={copy} aria-label="Copy response" title="Copy">
              {copied ? <Check size={15} /> : <Copy size={15} />}
            </button>
          )}
          {isLast && (
            <button className="icon-btn sm" onClick={onRetry} aria-label="Retry" title="Retry">
              <Retry size={15} />
            </button>
          )}
          {msg.llm && (
            <span className="msg-meta">
              {msg.llm.model}
              {msg.llm.time_to_first_token_ms != null && <> · first token {fmt.ms(msg.llm.time_to_first_token_ms)}</>}
              {" · "}
              {fmt.ms(msg.llm.latency_ms + (msg.compression?.telemetry.compression_latency_ms ?? 0))} total
            </span>
          )}
        </div>
      )}
    </div>
  );
}
