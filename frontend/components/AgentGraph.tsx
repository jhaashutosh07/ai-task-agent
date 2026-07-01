"use client";

import { Brain, Search, Code2, BarChart3, Terminal, Check, X } from "lucide-react";
import { AgentEvent } from "@/lib/types";

type NodeState = "idle" | "active" | "done" | "failed";

const AGENTS = [
  { key: "researcher", label: "Researcher", icon: Search },
  { key: "coder", label: "Coder", icon: Code2 },
  { key: "analyst", label: "Analyst", icon: BarChart3 },
  { key: "executor", label: "Executor", icon: Terminal },
];

function deriveStates(events: AgentEvent[]) {
  let orchestrator: NodeState = "idle";
  const agents: Record<string, NodeState> = {
    researcher: "idle", coder: "idle", analyst: "idle", executor: "idle",
  };
  let caption = "";
  for (const e of events) {
    const t = e.type || "";
    const a = (e.agent || e.data?.agent || "").toLowerCase();
    if (t === "orchestrator_start") { orchestrator = "active"; caption = "Analysing request"; }
    else if (t === "decomposing") { orchestrator = "active"; caption = "Planning subtasks"; }
    else if (t === "task_decomposed") { caption = "Plan ready"; }
    else if (t === "subtask_start") {
      const ag = (e.data?.agent || "").toLowerCase();
      if (ag in agents) agents[ag] = "active";
      caption = e.data?.description || `${ag} working`;
    }
    else if (t === "subtask_complete") {
      const ag = (e.data?.agent || "").toLowerCase();
      if (ag in agents) agents[ag] = e.data?.success === false ? "failed" : "done";
    }
    else if (t === "synthesizing") { orchestrator = "active"; caption = "Synthesising answer"; }
    else if (t === "orchestrator_complete") { orchestrator = "done"; caption = "Complete"; }
    else if (t.endsWith("_error")) { orchestrator = "failed"; }
    if (a && a in agents && agents[a] === "idle") agents[a] = "active";
  }
  return { orchestrator, agents, caption };
}

function nodeClass(s: NodeState) {
  switch (s) {
    case "active": return "border-primary-400 bg-primary-50 dark:bg-primary-500/15 text-primary-600 dark:text-primary-300 shadow-glow scale-105";
    case "done": return "border-emerald-300 bg-emerald-50 dark:bg-emerald-500/15 text-emerald-600 dark:text-emerald-300";
    case "failed": return "border-rose-300 bg-rose-50 dark:bg-rose-500/15 text-rose-600 dark:text-rose-300";
    default: return "border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-400";
  }
}

export default function AgentGraph({ events }: { events: AgentEvent[] }) {
  const { orchestrator, agents, caption } = deriveStates(events);
  const anyActive = orchestrator !== "idle" || Object.values(agents).some((s) => s !== "idle");
  if (!anyActive) return null;

  return (
    <div className="w-full rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white/60 dark:bg-zinc-900/60 backdrop-blur p-4 animate-fade-in">
      {/* Orchestrator */}
      <div className="flex flex-col items-center">
        <div className={`flex items-center gap-2 px-3.5 py-2 rounded-xl border-2 transition-all duration-300 ${nodeClass(orchestrator)}`}>
          <Brain className={`w-4 h-4 ${orchestrator === "active" ? "pulse-dot" : ""}`} />
          <span className="text-sm font-semibold">Orchestrator</span>
          {orchestrator === "done" && <Check className="w-3.5 h-3.5 text-emerald-500" />}
          {orchestrator === "failed" && <X className="w-3.5 h-3.5 text-rose-500" />}
        </div>
        {/* connector */}
        <div className="w-px h-4 bg-zinc-200 dark:bg-zinc-700" />
      </div>

      {/* Agents row */}
      <div className="grid grid-cols-4 gap-2">
        {AGENTS.map((ag) => {
          const s = agents[ag.key];
          return (
            <div key={ag.key} className={`flex flex-col items-center gap-1.5 px-2 py-2.5 rounded-xl border-2 transition-all duration-300 ${nodeClass(s)}`}>
              <ag.icon className={`w-4 h-4 ${s === "active" ? "pulse-dot" : ""}`} />
              <span className="text-[11px] font-medium">{ag.label}</span>
              {s === "active" && <span className="w-1.5 h-1.5 rounded-full bg-primary-400 pulse-dot" />}
              {s === "done" && <Check className="w-3 h-3 text-emerald-500" />}
              {s === "failed" && <X className="w-3 h-3 text-rose-500" />}
            </div>
          );
        })}
      </div>

      {caption && (
        <p className="text-xs text-zinc-500 dark:text-zinc-400 text-center mt-3 truncate">{caption}</p>
      )}
    </div>
  );
}
