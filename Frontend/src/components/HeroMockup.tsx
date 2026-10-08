"use client";

import { useState } from "react";
import type { ReactNode } from "react";

type Screen = "home" | "agents";

const INK = "#1a1814";
const MUTED = "#6b6560";
const FAINT = "#8f8778";
const LINE = "#e8e2d8";
const CORAL = "#c86018";

function Icon({ d, size = 14, color = FAINT }: { d: string; size?: number; color?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"
      style={{ width: size, height: size, flexShrink: 0 }}>
      <path d={d} />
    </svg>
  );
}

const ICONS = {
  home: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  inbox: "M22 12h-6l-2 3h-4l-2-3H2M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z",
  jobs: "M3 3h18v18H3zM9 3v18M15 3v18",
  projects: "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
  agents: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  glossary: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M8 13h8M8 17h5",
  flow: "M6 3v12M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM18 9a9 9 0 0 1-9 9",
  puzzle: "M12 2a2 2 0 0 1 2 2v1h4a2 2 0 0 1 2 2v4h-1a2 2 0 1 0 0 4h1v4a2 2 0 0 1-2 2h-4v-1a2 2 0 1 0-4 0v1H6a2 2 0 0 1-2-2v-4h1a2 2 0 1 0 0-4H4V7a2 2 0 0 1 2-2h4V4a2 2 0 0 1 2-2z",
  search: "M21 21l-4.3-4.3M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z",
  plus: "M12 5v14M5 12h14",
  arrow: "M7 17L17 7M8 7h9v9",
};

function Badge({ children }: { children: ReactNode }) {
  return <span style={{ marginLeft: "auto", fontSize: "10.5px", color: FAINT }}>{children}</span>;
}

function NavItem({ label, icon, active, onClick, badge }: {
  label: string; icon: string; active?: boolean; onClick?: () => void; badge?: string;
}) {
  return (
    <button type="button" onClick={onClick} className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left"
      style={{ background: active ? "#d6d0c4" : "transparent", cursor: onClick ? "pointer" : "default", border: 0 }}>
      <Icon d={icon} color={active ? INK : FAINT} />
      <span style={{ fontSize: "12.5px", color: active ? INK : MUTED, fontWeight: active ? 600 : 400 }}>{label}</span>
      {badge ? <Badge>{badge}</Badge> : null}
    </button>
  );
}

function Sidebar({ screen, go }: { screen: Screen; go: (s: Screen) => void }) {
  return (
    <div className="hidden shrink-0 flex-col md:flex" style={{ width: "214px", padding: "10px 8px" }}>
      <div className="px-2 pb-3 pt-1">
        <span style={{ fontFamily: "var(--font-share-tech-mono), monospace", fontSize: "14px", letterSpacing: "0.04em" }}>
          <span style={{ color: "#3a3630" }}>page</span><span style={{ color: "#e08a6f" }}>birdy</span>
        </span>
      </div>
      <NavItem label="Home" icon={ICONS.home} active={screen === "home"} onClick={() => go("home")} />
      <div style={{ height: "14px" }} />
      <NavItem label="Inbox" icon={ICONS.inbox} />
      <NavItem label="Jobs" icon={ICONS.jobs} />
      <NavItem label="Projects" icon={ICONS.projects} />
      <div style={{ height: "14px" }} />
      <NavItem label="Agents" icon={ICONS.agents} active={screen === "agents"} onClick={() => go("agents")} />
      <NavItem label="Glossary" icon={ICONS.glossary} />
      <NavItem label="Workflows" icon={ICONS.flow} badge="Beta" />
      <div style={{ fontSize: "10.5px", color: FAINT, padding: "16px 10px 6px" }}>Labs</div>
      <NavItem label="Extension" icon={ICONS.puzzle} badge="New" />
      <div className="mt-auto flex items-center gap-2 px-2 pt-3" style={{ borderTop: "1px solid #d3ccbf" }}>
        <span className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold text-white"
          style={{ background: "linear-gradient(135deg,#6b9cf4,#8b6fbf)" }}>A</span>
        <span style={{ fontSize: "12.5px", color: INK }}>Alex Chen</span>
      </div>
    </div>
  );
}

function PanelHeader({ icon, title, count, desc, right }: {
  icon: string; title: string; count?: number; desc?: string; right?: ReactNode;
}) {
  return (
    <div className="flex items-center gap-2.5 px-5 pt-4">
      <Icon d={icon} color={MUTED} />
      <span style={{ fontSize: "13.5px", fontWeight: 600, color: INK }}>{title}</span>
      {count !== undefined ? <span style={{ fontSize: "12px", color: FAINT }}>{count}</span> : null}
      {desc ? <span className="hidden lg:inline" style={{ fontSize: "12px", color: FAINT, marginLeft: "6px" }}>{desc}</span> : null}
      <div className="ml-auto">{right}</div>
    </div>
  );
}

const SUGGESTIONS = ["Which jobs need review before Friday?", "Translate the Q4 deck into French", "Which formats is the team using most?"];
const TODOS = ["Review the Arabic RTL proof", "Upload the brand glossary for German"];
const NEEDS = [
  { name: "Karen Holt", note: "Status on PB-214 — q4_campaign_deck.idml", time: "45 min ago", tint: "#f5b942" },
  { name: "Priya Raman", note: "Re: Japanese brand guide approval", time: "51 min ago", tint: "#8b6fbf" },
];

function Home() {
  return (
    <>
      <PanelHeader icon={ICONS.home} title="Home" />
      <div className="mx-auto w-full max-w-[560px] px-6" style={{ marginTop: "56px" }}>
        <h3 className="text-center" style={{ fontSize: "20px", fontWeight: 500, color: INK }}>Good evening, Alex</h3>
        <div className="mt-6 rounded-2xl p-4" style={{ background: "#f6f2ea", border: `1px solid ${LINE}` }}>
          <div style={{ fontSize: "13px", color: FAINT }}>Message Layout Agent…</div>
          <div className="mt-6 flex items-center gap-3" style={{ fontSize: "12px", color: MUTED }}>
            <Icon d={ICONS.plus} size={13} />
            <span className="inline-block h-3.5 w-3.5 rounded-full" style={{ background: "#e8ac2e" }} />
            <span>Layout Agent</span>
            <span className="ml-auto">Auto</span>
            <span className="flex h-6 w-6 items-center justify-center rounded-full" style={{ background: CORAL }}>
              <Icon d="M12 19V5M5 12l7-7 7 7" size={12} color="#fff" />
            </span>
          </div>
        </div>
        <div className="mt-6" style={{ fontSize: "11px", color: FAINT }}>Suggested next steps</div>
        {SUGGESTIONS.map((s) => (
          <div key={s} className="flex items-center justify-between py-2" style={{ fontSize: "12.5px", color: MUTED, borderBottom: `1px solid ${LINE}` }}>
            <span>{s}</span><Icon d={ICONS.arrow} size={11} />
          </div>
        ))}
      </div>

      <div className="mt-auto grid grid-cols-1 gap-5 px-5 pb-4 pt-8 lg:grid-cols-2" style={{ marginTop: "40px" }}>
        <div>
          <div style={{ fontSize: "10.5px", letterSpacing: "0.08em", color: FAINT, marginBottom: "8px" }}>WIDGETS</div>
          <div className="mb-2 flex items-center justify-between" style={{ fontSize: "13px", fontWeight: 600, color: INK }}>
            Todo <Icon d={ICONS.arrow} size={11} />
          </div>
          <div className="mb-2 flex items-center gap-2">
            <div className="flex-1 rounded-full px-3 py-1.5" style={{ background: "#f6f2ea", fontSize: "12px", color: FAINT }}>Capture a todo…</div>
            <span className="flex h-6 w-6 items-center justify-center rounded-full" style={{ background: "#ece6da" }}><Icon d={ICONS.plus} size={12} color={MUTED} /></span>
          </div>
          {TODOS.map((t) => (
            <div key={t} className="mb-1.5 flex items-center gap-2.5 rounded-xl px-3 py-2" style={{ background: "#f6f2ea", fontSize: "12.5px", color: INK }}>
              <span className="inline-block h-3.5 w-3.5 rounded" style={{ border: "1.5px solid #cfc6b6", background: "#fff" }} />{t}
            </div>
          ))}
        </div>
        <div className="lg:pt-[22px]">
          <div className="mb-2 flex items-center justify-between" style={{ fontSize: "13px", fontWeight: 600, color: INK }}>
            Needs to know <Icon d={ICONS.arrow} size={11} />
          </div>
          {NEEDS.map((n) => (
            <div key={n.name} className="mb-1.5 flex items-center gap-3 rounded-xl px-3 py-2.5" style={{ background: "#f6f2ea" }}>
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white" style={{ background: n.tint }}>
                {n.name.split(" ").map((p) => p[0]).join("")}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex justify-between" style={{ fontSize: "12.5px", color: INK, fontWeight: 600 }}>
                  {n.name}<span style={{ fontSize: "11px", color: FAINT, fontWeight: 400 }}>{n.time}</span>
                </div>
                <div className="truncate" style={{ fontSize: "12px", color: MUTED }}>{n.note}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

const AGENTS = [
  { name: "Layout Agent", tag: "system", desc: "Rebuilds frames, styles and masters.", runs: 214, color: "#e0527a", bars: [3, 5, 4, 7, 6, 8, 5] },
  { name: "Timecode Agent", tag: "", desc: "Keeps every cue on its timecode.", runs: 61, color: "#a98bf0", bars: [6, 4, 7, 3, 6, 4, 7] },
  { name: "OCR Agent", tag: "", desc: "Reads and re-renders text in images.", runs: 132, color: "#f5b942", bars: [4, 6, 5, 7, 4, 7, 5] },
  { name: "Web Agent", tag: "", desc: "Translates a public page, keeps the markup.", runs: 46, color: "#e8ac2e", bars: [3, 4, 6, 3, 5, 3, 2] },
];

function Agents() {
  return (
    <>
      <PanelHeader icon={ICONS.agents} title="Agents" count={4} desc="Agents that turn approved work into files, comments and status changes."
        right={<span className="rounded-full px-3 py-1.5" style={{ fontSize: "12px", color: INK, border: `1px solid ${LINE}`, background: "#fff" }}>+ New agent</span>} />
      <div className="flex items-center justify-between px-5 pt-4">
        <div className="flex rounded-full p-0.5" style={{ background: "#f0ece3", fontSize: "12px" }}>
          {["Agents", "Skills", "Connections"].map((t, i) => (
            <span key={t} className="rounded-full px-3 py-1" style={{ background: i === 0 ? "#fff" : "transparent", color: i === 0 ? INK : MUTED, boxShadow: i === 0 ? "0 1px 2px rgba(0,0,0,0.08)" : "none" }}>{t}</span>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-full p-0.5" style={{ background: "#f0ece3", fontSize: "12px" }}>
            <span className="rounded-full px-3 py-1" style={{ background: "#fff", color: INK, boxShadow: "0 1px 2px rgba(0,0,0,0.08)" }}>Active</span>
            <span className="px-3 py-1" style={{ color: MUTED }}>Archived 2</span>
          </div>
          <Icon d={ICONS.search} size={14} color={MUTED} />
        </div>
      </div>

      <div className="px-5 pt-6">
        <div className="grid items-center px-2 pb-2" style={{ gridTemplateColumns: "minmax(0,1fr) 70px 80px 110px 60px 24px", fontSize: "11.5px", color: MUTED }}>
          <span>Agent</span><span>Status</span><span className="hidden sm:block">Workload</span><span className="hidden sm:block">Activity 7d</span><span className="text-right">Runs</span><span />
        </div>
        {AGENTS.map((a) => (
          <div key={a.name} className="grid items-center px-2 py-3" style={{ gridTemplateColumns: "minmax(0,1fr) 70px 80px 110px 60px 24px", borderTop: `1px solid ${LINE}` }}>
            <div className="flex min-w-0 items-center gap-3">
              <span className="h-7 w-7 shrink-0" style={{ background: a.color, borderRadius: "50% 50% 46% 46%" }} />
              <div className="min-w-0">
                <div className="flex items-center gap-2" style={{ fontSize: "13px", fontWeight: 600, color: INK }}>
                  {a.name}
                  {a.tag ? <span className="rounded-md px-1.5" style={{ fontSize: "10.5px", fontWeight: 400, color: MUTED, background: "#f0ece3" }}>{a.tag}</span> : null}
                </div>
                <div className="truncate" style={{ fontSize: "12px", color: MUTED }}>{a.desc}</div>
              </div>
            </div>
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#4caf50" }} />
            <span className="hidden sm:block" style={{ fontSize: "12px", color: MUTED }}>0/1</span>
            <svg viewBox="0 0 56 16" className="hidden sm:block" style={{ width: "56px", height: "16px" }}>
              {a.bars.map((h, i) => <rect key={i} x={i * 8} y={16 - h * 2} width="6" height={h * 2} fill="#cfc6b6" rx="1" />)}
            </svg>
            <span className="text-right" style={{ fontSize: "12.5px", color: MUTED }}>{a.runs}</span>
            <span style={{ color: FAINT, textAlign: "center" }}>⋮</span>
          </div>
        ))}
      </div>
    </>
  );
}

export default function HeroMockup() {
  const [screen, setScreen] = useState<Screen>("home");
  return (
    <div className="pb-mock relative mt-16 lg:-mx-20 xl:-mx-32" style={{
      borderRadius: "18px",
      background: "#e2ddd6",
      boxShadow: "0 60px 160px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,0,0,0.12)",
    }}>
      <div className="pb-mock-fill pb-mock-fill-1 flex items-center gap-2 px-5 py-3" style={{ background: "#e8e2d8", borderBottom: "1px solid #d8d2c8", borderRadius: "18px 18px 0 0" }}>
        <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#ff5f57" }} />
        <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#febc2e" }} />
        <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#28c840" }} />
        <span style={{ marginLeft: "12px", fontSize: "12px", color: "#9a9284", fontWeight: 500 }}>Pagebirdy</span>
      </div>

      <div className="flex gap-2 p-2" style={{ minHeight: "640px" }}>
        <div className="pb-mock-content hidden md:flex"><Sidebar screen={screen} go={setScreen} /></div>
        <div className="pb-mock-fill pb-mock-fill-2 flex min-w-0 flex-1 flex-col" style={{ background: "#ffffff", borderRadius: "14px" }}>
          <div className="pb-mock-content flex min-w-0 flex-1 flex-col">{screen === "home" ? <Home /> : <Agents />}</div>
        </div>
      </div>

      <div className="pointer-events-none absolute bottom-0 left-0 right-0" style={{
        height: "32%", borderRadius: "0 0 18px 18px",
        background: "linear-gradient(to top, #45588e 0%, #45588e 5%, rgba(69,88,142,0.85) 40%, transparent 100%)",
      }} />
    </div>
  );
}
