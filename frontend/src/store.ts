import type { Attachment, Conversation, ConvSettings, GlobalSettings } from "./types";

const CONV_KEY = "prompt-budget.conversations.v1";
const SETTINGS_KEY = "prompt-budget.settings.v1";

export const DEFAULT_SYSTEM =
  "Answer using only the supplied context. Be concise and precise. If the answer is not in the context, say that it is unknown.";

export const DEFAULT_SETTINGS: GlobalSettings = {
  systemInstruction: DEFAULT_SYSTEM,
  temperature: 0,
  model: null,
  theme: "system",
};

export const DEFAULT_CONV_SETTINGS: ConvSettings = {
  targetRatio: 2,
  tokenBudget: null,
  task: "unspecified",
  systemInstruction: null,
};

export const uid = () =>
  (crypto.randomUUID?.() ?? Math.random().toString(36).slice(2) + Date.now().toString(36));

export function newConversation(settings?: Partial<ConvSettings>): Conversation {
  const now = Date.now();
  return {
    id: uid(),
    title: "New chat",
    createdAt: now,
    updatedAt: now,
    attachments: [],
    messages: [],
    settings: { ...DEFAULT_CONV_SETTINGS, ...settings },
  };
}

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage full or unavailable: state stays in memory for this session */
  }
}

export function loadConversations(): Conversation[] {
  const convs = read<Conversation[]>(CONV_KEY, []);
  // Any reply still "in flight" when the page closed can't resume.
  return convs.map((c) => ({
    ...c,
    messages: c.messages.map((m) =>
      m.role === "assistant" && (m.status === "compressing" || m.status === "generating")
        ? { ...m, status: "stopped" as const }
        : m,
    ),
  }));
}

export const saveConversations = (convs: Conversation[]) => write(CONV_KEY, convs);
export const loadSettings = (): GlobalSettings => ({ ...DEFAULT_SETTINGS, ...read(SETTINGS_KEY, {}) });
export const saveSettings = (s: GlobalSettings) => write(SETTINGS_KEY, s);

/** Join attachments into the single context string the middleware compresses. */
export function buildContext(attachments: Attachment[]): string {
  if (attachments.length === 1) return attachments[0].text;
  return attachments.map((a) => `### ${a.name}\n${a.text}`).join("\n\n");
}

export const fmt = {
  int: (n: number | null | undefined) => (n == null ? "—" : Math.round(n).toLocaleString()),
  ratio: (n: number | null | undefined) => (n == null ? "—" : `${n.toFixed(2)}×`),
  ms: (n: number | null | undefined) =>
    n == null ? "—" : n >= 1000 ? `${(n / 1000).toFixed(1)} s` : `${Math.round(n)} ms`,
  pct: (n: number | null | undefined) => (n == null ? "—" : `${n.toFixed(1)}%`),
};

export const TASK_LABELS: Record<string, string> = {
  unspecified: "General",
  extractive_qa: "Extractive QA",
  multi_hop_qa: "Multi-hop QA",
  summarization: "Summarization",
};
