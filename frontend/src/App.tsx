import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { api, streamChat } from "./api";
import {
  TASK_LABELS,
  buildContext,
  loadConversations,
  loadSettings,
  newConversation,
  saveConversations,
  saveSettings,
  uid,
} from "./store";
import type {
  AssistantMessage,
  Attachment,
  Conversation,
  ConvSettings,
  GlobalSettings,
  Health,
  Message,
  Sample,
  UserMessage,
} from "./types";
import { Composer } from "./components/Composer";
import { MessageView } from "./components/MessageView";
import { Sidebar } from "./components/Sidebar";
import { BenchmarksView } from "./components/BenchmarksView";
import { AttachmentDialog, SettingsDialog } from "./components/Dialogs";
import { Alert, Mark, Sidebar as SidebarIcon } from "./components/Icons";

const MOBILE = "(max-width: 767px)";

function greeting() {
  const h = new Date().getHours();
  if (h < 5) return "Burning the midnight oil";
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function titleFrom(text: string) {
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > 48 ? clean.slice(0, 46).trimEnd() + "…" : clean || "New chat";
}

const estimateTokens = (text: string) => Math.ceil(text.length / 4);

export default function App() {
  const [convs, setConvs] = useState<Conversation[]>(loadConversations);
  const [draft, setDraft] = useState<Conversation>(() => newConversation());
  const [activeId, setActiveId] = useState<string | null>(null);
  const [view, setView] = useState<"chat" | "benchmarks">("chat");
  const [settings, setSettings] = useState<GlobalSettings>(loadSettings);
  const [sidebarOpen, setSidebarOpen] = useState(() => !window.matchMedia(MOBILE).matches);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [uploading, setUploading] = useState<string[]>([]);
  const [preview, setPreview] = useState<Attachment | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const threadRef = useRef<HTMLDivElement>(null);
  const stickToBottom = useRef(true);

  const active = activeId ? convs.find((c) => c.id === activeId) ?? null : null;
  const current = active ?? draft;
  const busy = busyId === current.id;

  // ---------------------------------------------------------------- effects
  useEffect(() => {
    const t = setTimeout(() => saveConversations(convs), 400);
    return () => clearTimeout(t);
  }, [convs]);

  useEffect(() => saveSettings(settings), [settings]);

  useEffect(() => {
    const root = document.documentElement;
    if (settings.theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", settings.theme);
  }, [settings.theme]);

  useEffect(() => {
    let alive = true;
    const tick = () =>
      api
        .health()
        .then((h) => {
          if (!alive) return;
          setHealth(h);
          setHealthError(null);
        })
        .catch((e: Error) => alive && setHealthError(e.message || "unreachable"));
    tick();
    const iv = setInterval(tick, 15_000);
    return () => {
      alive = false;
      clearInterval(iv);
    };
  }, []);

  useEffect(() => {
    api.samples(6).then((r) => setSamples(r.samples)).catch(() => setSamples([]));
  }, [healthError == null]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(t);
  }, [toast]);

  // Keep the thread pinned to the bottom while streaming, unless the user scrolled up.
  useLayoutEffect(() => {
    const el = threadRef.current;
    if (el && stickToBottom.current) el.scrollTop = el.scrollHeight;
  }, [current.messages]);

  useLayoutEffect(() => {
    stickToBottom.current = true;
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [current.id, view]);

  // ---------------------------------------------------------------- model choice
  const models = health?.llm.models ?? [];
  let model: string | null = settings.model;
  if (!model || (models.length > 0 && !models.includes(model))) {
    const def = health?.llm.default_model ?? null;
    model = def && (models.length === 0 || models.includes(def)) ? def : models[0] ?? def;
  }

  // ---------------------------------------------------------------- state helpers
  const updateConv = useCallback((id: string, fn: (c: Conversation) => Conversation) => {
    setDraft((d) => (d.id === id ? fn(d) : d));
    setConvs((cs) => cs.map((c) => (c.id === id ? fn(c) : c)));
  }, []);

  const closeSidebarOnMobile = () => {
    if (window.matchMedia(MOBILE).matches) setSidebarOpen(false);
  };

  const addAttachment = (convId: string, a: Attachment) =>
    updateConv(convId, (c) => ({ ...c, attachments: [...c.attachments, a] }));

  const addFiles = (convId: string, files: File[]) => {
    files.forEach(async (file) => {
      setUploading((u) => [...u, file.name]);
      try {
        const r = await api.ingest(file);
        addAttachment(convId, { id: uid(), name: file.name, kind: "file", text: r.text, tokens: r.tokens });
      } catch (e) {
        setToast(`Couldn't read ${file.name}: ${(e as Error).message}`);
      } finally {
        setUploading((u) => u.filter((n) => n !== file.name));
      }
    });
  };

  const addPaste = async (convId: string, text: string) => {
    const tokens = await api.tokens(text).then((r) => r.tokens).catch(() => estimateTokens(text));
    const n = current.attachments.filter((a) => a.kind === "paste").length + 1;
    addAttachment(convId, { id: uid(), name: n > 1 ? `Pasted text ${n}` : "Pasted text", kind: "paste", text, tokens });
  };

  // ---------------------------------------------------------------- chat
  const run = async (conv: Conversation, question: string, history: Message[], asstId: string) => {
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setBusyId(conv.id);

    const patch = (p: Partial<AssistantMessage> | ((m: AssistantMessage) => Partial<AssistantMessage>)) =>
      updateConv(conv.id, (c) => ({
        ...c,
        updatedAt: Date.now(),
        messages: c.messages.map((m) =>
          m.id === asstId && m.role === "assistant" ? { ...m, ...(typeof p === "function" ? p(m) : p) } : m,
        ),
      }));

    const turns = history
      .filter((m) => m.role === "user" || (m.status === "done" && m.content))
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      await streamChat(
        {
          system_instruction: conv.settings.systemInstruction ?? settings.systemInstruction,
          question,
          context: buildContext(conv.attachments),
          target_ratio: conv.settings.targetRatio,
          token_budget: conv.settings.tokenBudget,
          task: conv.settings.task,
          model,
          temperature: settings.temperature,
          history: turns,
        },
        (ev) => {
          switch (ev.type) {
            case "status":
              patch({ status: ev.stage });
              break;
            case "compression":
              patch({
                compression: { context: ev.context, telemetry: ev.telemetry, compressor_metadata: ev.compressor_metadata },
              });
              break;
            case "token":
              patch((m) => ({ content: m.content + ev.text }));
              break;
            case "done":
              patch({ status: "done", llm: ev.llm });
              break;
            case "error":
              patch({ status: "error", error: ev.message });
              break;
          }
        },
        ctrl.signal,
      );
      patch((m) =>
        m.status === "compressing" || m.status === "generating"
          ? { status: "error", error: "The response stream ended unexpectedly." }
          : {},
      );
    } catch (e) {
      if (ctrl.signal.aborted) patch({ status: "stopped" });
      else patch({ status: "error", error: (e as Error).message || "Request failed" });
    } finally {
      if (abortRef.current === ctrl) {
        abortRef.current = null;
        setBusyId(null);
      }
    }
  };

  const sendIn = (conv: Conversation, text: string) => {
    if (busyId) return;
    const user: UserMessage = { id: uid(), role: "user", content: text, createdAt: Date.now() };
    const asst: AssistantMessage = {
      id: uid(),
      role: "assistant",
      content: "",
      createdAt: Date.now(),
      status: "compressing",
      targetRatio: conv.settings.targetRatio,
      tokenBudget: conv.settings.tokenBudget,
    };
    const next: Conversation = {
      ...conv,
      title: conv.messages.length === 0 ? titleFrom(text) : conv.title,
      updatedAt: Date.now(),
      messages: [...conv.messages, user, asst],
    };
    if (convs.some((c) => c.id === conv.id)) {
      updateConv(conv.id, () => next);
    } else {
      setConvs((cs) => [next, ...cs]);
      setActiveId(next.id);
      setDraft(newConversation());
    }
    stickToBottom.current = true;
    void run(next, text, conv.messages, asst.id);
  };

  const retry = () => {
    if (!active || busyId) return;
    const msgs = active.messages;
    let i = msgs.length - 1;
    while (i >= 0 && msgs[i].role !== "user") i--;
    if (i < 0) return;
    const asst: AssistantMessage = {
      id: uid(),
      role: "assistant",
      content: "",
      createdAt: Date.now(),
      status: "compressing",
      targetRatio: active.settings.targetRatio,
      tokenBudget: active.settings.tokenBudget,
    };
    const next = { ...active, updatedAt: Date.now(), messages: [...msgs.slice(0, i + 1), asst] };
    updateConv(active.id, () => next);
    void run(next, msgs[i].content, msgs.slice(0, i), asst.id);
  };

  const stop = () => abortRef.current?.abort();

  const trySample = async (s: Sample) => {
    const tokens = await api.tokens(s.context).then((r) => r.tokens).catch(() => estimateTokens(s.context));
    const conv: Conversation = {
      ...current,
      attachments: [...current.attachments, { id: uid(), name: `${s.id}.log`, kind: "sample", text: s.context, tokens }],
      settings: { ...current.settings, task: s.task, systemInstruction: s.system_instruction },
    };
    sendIn(conv, s.question);
  };

  const deleteConv = (id: string) => {
    if (busyId === id) stop();
    setConvs((cs) => cs.filter((c) => c.id !== id));
    if (activeId === id) setActiveId(null);
  };

  const setConvSettings = (s: Partial<ConvSettings>) =>
    updateConv(current.id, (c) => ({ ...c, settings: { ...c.settings, ...s } }));

  // ---------------------------------------------------------------- render
  const empty = current.messages.length === 0;
  const composer = (
    <Composer
      busy={busy}
      attachments={current.attachments}
      uploading={uploading}
      settings={current.settings}
      models={models}
      model={model}
      connecting={!health && !healthError}
      autoFocus={view === "chat"}
      placeholder={empty ? "Paste logs, attach a document, or ask anything…" : "Reply…"}
      onSend={(t) => sendIn(current, t)}
      onStop={stop}
      onAddFiles={(f) => addFiles(current.id, f)}
      onAddPaste={(t) => void addPaste(current.id, t)}
      onRemoveAttachment={(id) =>
        updateConv(current.id, (c) => ({ ...c, attachments: c.attachments.filter((a) => a.id !== id) }))
      }
      onPreviewAttachment={setPreview}
      onSettingsChange={setConvSettings}
      onModelChange={(m) => setSettings((s) => ({ ...s, model: m }))}
    />
  );

  const banner = healthError ? (
    <div className="banner">
      <Alert size={15} />
      <span>
        Can't reach the API. Start it from the repo root: <code>uvicorn prompt_budget.api:app --reload</code>
      </span>
    </div>
  ) : health && !health.llm.reachable ? (
    <div className="banner">
      <Alert size={15} />
      <span>
        Ollama isn't reachable at <code>{health.llm.base_url}</code>. Run <code>ollama serve</code>.
      </span>
    </div>
  ) : null;

  return (
    <div className={"app" + (sidebarOpen ? " sidebar-open" : "")}>
      <Sidebar
        open={sidebarOpen}
        conversations={convs}
        activeId={activeId}
        view={view}
        health={health}
        healthError={healthError}
        onToggle={() => setSidebarOpen((o) => !o)}
        onNew={() => {
          setActiveId(null);
          setView("chat");
          closeSidebarOnMobile();
        }}
        onSelect={(id) => {
          setActiveId(id);
          setView("chat");
          closeSidebarOnMobile();
        }}
        onDelete={deleteConv}
        onBenchmarks={() => {
          setView("benchmarks");
          closeSidebarOnMobile();
        }}
        onSettings={() => setShowSettings(true)}
      />
      {sidebarOpen && <div className="scrim" onClick={() => setSidebarOpen(false)} />}

      <main
        className="main"
        onDragOver={(e) => {
          if (view !== "chat" || !e.dataTransfer.types.includes("Files")) return;
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={(e) => {
          if (e.currentTarget === e.target) setDragging(false);
        }}
        onDrop={(e) => {
          if (view !== "chat") return;
          e.preventDefault();
          setDragging(false);
          const files = Array.from(e.dataTransfer.files);
          if (files.length) addFiles(current.id, files);
        }}
      >
        <header className="topbar">
          <button className="icon-btn mobile-only" onClick={() => setSidebarOpen(true)} aria-label="Open sidebar">
            <SidebarIcon />
          </button>
          {view === "chat" && !empty && (
            <div className="topbar-title">
              <span>{current.title}</span>
              {current.settings.task !== "unspecified" && (
                <span className="tag">{TASK_LABELS[current.settings.task]}</span>
              )}
            </div>
          )}
        </header>

        {view === "benchmarks" ? (
          <BenchmarksView />
        ) : empty ? (
          <div className="welcome">
            <div className="welcome-inner">
              <h1 className="welcome-title">
                <Mark size={34} />
                <span>{greeting()}</span>
              </h1>
              <p className="welcome-sub">
                Attach logs or documents, pick a compression ratio, and ask. Only the context gets compressed — your
                question and instructions stay intact.
              </p>
              {banner}
              {composer}
              {samples.length > 0 && (
                <div className="samples">
                  <div className="samples-label">Try a benchmark case</div>
                  <div className="sample-grid">
                    {samples.map((s) => (
                      <button key={s.id} className="sample" onClick={() => void trySample(s)} disabled={!!busyId}>
                        <span className="sample-task">{TASK_LABELS[s.task] ?? s.task}</span>
                        <span className="sample-q">{s.question}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <>
            <div
              className="thread"
              ref={threadRef}
              onScroll={(e) => {
                const el = e.currentTarget;
                stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
              }}
            >
              <div className="thread-inner">
                {current.messages.map((m, i) => (
                  <MessageView key={m.id} msg={m} isLast={i === current.messages.length - 1} onRetry={retry} />
                ))}
              </div>
            </div>
            <div className="dock">
              <div className="dock-inner">
                {banner}
                {composer}
                <div className="dock-note">
                  Answers come from a local model and can be wrong. Compression can drop details.
                </div>
              </div>
            </div>
          </>
        )}

        {dragging && (
          <div className="dropzone">
            <div>Drop files to add them as context</div>
          </div>
        )}
        {toast && (
          <div className="toast" role="status">
            {toast}
          </div>
        )}
      </main>

      {preview && <AttachmentDialog attachment={preview} onClose={() => setPreview(null)} />}
      {showSettings && (
        <SettingsDialog
          settings={settings}
          health={health}
          healthError={healthError}
          onChange={(s) => setSettings((prev) => ({ ...prev, ...s }))}
          onClearAll={() => {
            stop();
            setConvs([]);
            setActiveId(null);
          }}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}
