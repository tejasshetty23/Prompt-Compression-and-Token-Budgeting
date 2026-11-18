import type { Conversation, Health } from "../types";
import { Chart, Gear, Mark, Plus, Sidebar as SidebarIcon, Trash } from "./Icons";

type Props = {
  open: boolean;
  conversations: Conversation[];
  activeId: string | null;
  view: "chat" | "benchmarks";
  health: Health | null;
  healthError: string | null;
  onToggle: () => void;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onBenchmarks: () => void;
  onSettings: () => void;
};

function groupLabel(ts: number) {
  const day = 86_400_000;
  const startToday = new Date().setHours(0, 0, 0, 0);
  if (ts >= startToday) return "Today";
  if (ts >= startToday - day) return "Yesterday";
  if (ts >= startToday - 7 * day) return "Previous 7 days";
  return "Older";
}

export function Sidebar(p: Props) {
  const groups: [string, Conversation[]][] = [];
  for (const c of [...p.conversations].sort((a, b) => b.updatedAt - a.updatedAt)) {
    const label = groupLabel(c.updatedAt);
    const g = groups.find(([l]) => l === label);
    if (g) g[1].push(c);
    else groups.push([label, [c]]);
  }

  let statusClass = "warn";
  let statusText = "Connecting…";
  if (p.healthError) {
    statusClass = "bad";
    statusText = "API offline";
  } else if (p.health) {
    statusClass = p.health.llm.reachable ? "good" : "bad";
    statusText = p.health.llm.reachable ? "Ollama connected" : "Ollama unreachable";
  }

  return (
    <aside className={"sidebar" + (p.open ? "" : " collapsed")}>
      <div className="sidebar-top">
        <button className="icon-btn" onClick={p.onToggle} aria-label={p.open ? "Close sidebar" : "Open sidebar"}>
          <SidebarIcon />
        </button>
        {p.open && (
          <div className="brand">
            <Mark size={20} />
            <span>Prompt Budget</span>
          </div>
        )}
      </div>

      <nav className="sidebar-nav">
        <button className="nav-item new-chat" onClick={p.onNew}>
          <span className="new-chat-icon"><Plus size={15} /></span>
          {p.open && <span>New chat</span>}
        </button>
        <button
          className={"nav-item" + (p.view === "benchmarks" ? " on" : "")}
          onClick={p.onBenchmarks}
          title="Benchmarks"
        >
          <Chart size={17} />
          {p.open && <span>Benchmarks</span>}
        </button>
      </nav>

      {p.open && (
        <div className="recents">
          {groups.length === 0 && <div className="recents-empty">Your chats will show up here.</div>}
          {groups.map(([label, items]) => (
            <div key={label} className="recents-group">
              <div className="recents-label">{label}</div>
              {items.map((c) => (
                <div
                  key={c.id}
                  className={"recent" + (p.view === "chat" && c.id === p.activeId ? " on" : "")}
                >
                  <button className="recent-title" onClick={() => p.onSelect(c.id)} title={c.title}>
                    {c.title}
                  </button>
                  <button
                    className="recent-delete"
                    aria-label={`Delete ${c.title}`}
                    onClick={() => p.onDelete(c.id)}
                  >
                    <Trash size={14} />
                  </button>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      <div className="sidebar-foot">
        <button className="nav-item" onClick={p.onSettings} title="Settings">
          <span className={"status-dot " + statusClass} />
          {p.open && (
            <span className="foot-text">
              <span>{statusText}</span>
              <span className="foot-sub">
                {p.health ? (p.health.compressor.loaded ? "LLMLingua-2 loaded" : "LLMLingua-2 loads on first use") : " "}
              </span>
            </span>
          )}
          {p.open && <Gear size={16} className="foot-gear" />}
        </button>
      </div>
    </aside>
  );
}
