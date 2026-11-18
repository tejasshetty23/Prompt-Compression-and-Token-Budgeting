import type { ChatEvent, Health, Sample, SummaryRow } from "./types";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => fetch("/api/health").then((r) => json<Health>(r)),

  samples: (limit = 6) =>
    fetch(`/api/samples?limit=${limit}`).then((r) => json<{ samples: Sample[] }>(r)),

  benchmarks: () =>
    fetch("/api/benchmarks").then((r) => json<{ summary: SummaryRow[]; figures: string[] }>(r)),

  tokens: (text: string) =>
    fetch("/api/tokens", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }).then((r) => json<{ tokens: number }>(r)),

  ingest: (file: File) =>
    fetch(`/api/ingest?filename=${encodeURIComponent(file.name)}`, {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: file,
    }).then((r) => json<{ filename: string; text: string; tokens: number }>(r)),
};

export type ChatPayload = {
  system_instruction: string;
  question: string;
  context: string;
  target_ratio: number;
  token_budget: number | null;
  task: string;
  model: string | null;
  temperature: number;
  history: { role: "user" | "assistant"; content: string }[];
};

/** POST /api/chat and dispatch each NDJSON event as it arrives. */
export async function streamChat(
  payload: ChatPayload,
  onEvent: (event: ChatEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok || !res.body) {
    await json(res);
    throw new Error("Empty response from /api/chat");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let newline: number;
    while ((newline = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (line) onEvent(JSON.parse(line) as ChatEvent);
    }
  }
  if (buffer.trim()) onEvent(JSON.parse(buffer) as ChatEvent);
}
