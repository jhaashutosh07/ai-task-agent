"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  User, Sparkles, ChevronDown, Wrench, Check, X,
  Zap, FileText, RefreshCw, Gauge, Loader2,
} from "lucide-react";
import { Message, AgentEvent, Citation, ChatMeta } from "@/lib/types";
import { evaluateAnswer } from "@/lib/api";
import CodeBlock from "./CodeBlock";

function EvalButton({ question, answer, context }: { question: string; answer: string; context: string }) {
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<any>(null);
  const run = async () => {
    setLoading(true);
    try { setRes(await evaluateAnswer(question, answer, context)); } catch { /* ignore */ }
    setLoading(false);
  };
  const color = (s: number) => (s >= 4 ? "text-emerald-500" : s >= 2.5 ? "text-amber-500" : "text-rose-500");
  if (res) {
    return (
      <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px]">
        {(["faithfulness", "relevance", "completeness"] as const).map((k) => (
          <span key={k} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
            <span className="text-zinc-400 capitalize">{k.slice(0, 4)}</span>
            <span className={`font-semibold ${color(res.scores?.[k] || 0)}`}>{(res.scores?.[k] || 0).toFixed(1)}</span>
          </span>
        ))}
        <span className={`font-semibold ${color(res.overall)}`}>★ {res.overall}/5</span>
        {res.verdict && <span className="text-zinc-400 italic">— {res.verdict}</span>}
      </div>
    );
  }
  return (
    <button onClick={run} disabled={loading} className="mt-2 inline-flex items-center gap-1.5 text-[11px] font-medium text-zinc-400 hover:text-primary-500 transition-colors">
      {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Gauge className="w-3 h-3" />}
      {loading ? "Evaluating…" : "Evaluate answer"}
    </button>
  );
}

// Map raw orchestrator/agent event types to readable step labels.
function stepLabel(e: AgentEvent): string | null {
  const t = e.type || "";
  const d = e.data || {};
  switch (t) {
    case "orchestrator_start": return "Analysing your request";
    case "decomposing": return "Planning subtasks";
    case "task_decomposed": return "Plan ready";
    case "subtask_start": return `${e.agent || "agent"}: ${d.description || ""}`.trim();
    case "subtask_complete": return `${e.agent || "agent"} finished`;
    case "synthesizing": return "Synthesising the answer";
    case "orchestrator_complete": return "Done";
    case "tool_call": return `Tool: ${d.tool || ""}`;
    case "tool_result": return `Tool result${d.tool ? `: ${d.tool}` : ""}`;
    default:
      if (t.endsWith("_error")) return `Error: ${d.error || ""}`.slice(0, 80);
      return null;
  }
}

function AgentActivity({ events }: { events: AgentEvent[] }) {
  const [open, setOpen] = useState(false);
  const steps = events
    .map((e) => ({ e, label: stepLabel(e) }))
    .filter((s) => s.label);
  if (steps.length === 0) return null;

  return (
    <div className="mt-2 w-full">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-xs font-medium text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors"
      >
        <Wrench className="w-3.5 h-3.5" />
        {steps.length} agent step{steps.length > 1 ? "s" : ""}
        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="mt-2 space-y-1.5 border-l-2 border-zinc-200 dark:border-zinc-700 pl-3 animate-slide-up">
          {steps.map(({ e, label }, i) => {
            const ok = e.data?.success;
            const isErr = (e.type || "").endsWith("_error");
            return (
              <div key={i} className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
                {isErr ? <X className="w-3 h-3 text-rose-500 flex-shrink-0" />
                  : ok === true ? <Check className="w-3 h-3 text-emerald-500 flex-shrink-0" />
                  : <span className="w-1.5 h-1.5 rounded-full bg-primary-400 flex-shrink-0" />}
                <span className="truncate">{label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Sources({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState(false);
  if (!citations || citations.length === 0) return null;
  return (
    <div className="mt-2 w-full">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-xs font-medium text-primary-500 hover:text-primary-600 transition-colors"
      >
        <FileText className="w-3.5 h-3.5" />
        {citations.length} source{citations.length > 1 ? "s" : ""}
        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="mt-2 space-y-2 animate-slide-up">
          {citations.map((c) => (
            <div key={c.n} className="text-xs bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-700 rounded-xl p-2.5">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-zinc-600 dark:text-zinc-300">
                  [{c.n}] {c.filename}
                </span>
                <span className="text-zinc-400">{(c.score * 100).toFixed(0)}%</span>
              </div>
              <p className="text-zinc-500 dark:text-zinc-400 leading-relaxed">{c.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MetaBadges({ meta }: { meta?: ChatMeta }) {
  if (!meta) return null;
  const badges: { icon: any; label: string; cls: string }[] = [];
  if (meta.cache_hit)
    badges.push({ icon: Zap, label: "cached", cls: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10" });
  if (meta.intent && meta.intent !== "cache")
    badges.push({ icon: Sparkles, label: meta.intent, cls: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-500/10" });
  if (meta.reflected)
    badges.push({ icon: RefreshCw, label: "refined", cls: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10" });
  if (badges.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
      {badges.map((b, i) => (
        <span key={i} className={`inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-md ${b.cls}`}>
          <b.icon className="w-2.5 h-2.5" />{b.label}
        </span>
      ))}
    </div>
  );
}

export default function MessageBubble({ message, question }: { message: Message; question?: string }) {
  const isUser = message.role === "user";
  const content = message.content || "";
  const events = message.events || [];
  const citations = message.citations || [];
  const images = message.images || [];
  const time = (() => {
    try { return new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }
    catch { return ""; }
  })();

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center ${
        isUser ? "bg-primary-100 dark:bg-primary-500/15" : "bg-gradient-to-br from-primary-500 to-violet-600"
      }`}>
        {isUser
          ? <User className="w-4 h-4 text-primary-600 dark:text-primary-400" />
          : <Sparkles className="w-4 h-4 text-white" />}
      </div>

      <div className={`max-w-[78%] flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
        {images.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-1">
            {images.map((src, i) => (
              <img key={i} src={src} alt="attachment" className="max-w-[220px] max-h-[220px] rounded-xl border border-zinc-200 dark:border-zinc-800 object-cover" />
            ))}
          </div>
        )}
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? "bg-primary-600 text-white rounded-tr-sm"
            : "bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-100 border border-zinc-200 dark:border-zinc-800 shadow-card rounded-tl-sm"
        }`}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <div className="markdown-content space-y-2">
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                  li: ({ children }) => <li>{children}</li>,
                  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                  h1: ({ children }) => <h1 className="text-base font-bold mb-1">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-sm font-bold mb-1">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-semibold mb-1">{children}</h3>,
                  code({ node, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || "");
                    if (!match) {
                      return <code className="bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>{children}</code>;
                    }
                    return <CodeBlock code={String(children).replace(/\n$/, "")} language={match[1]} />;
                  },
                }}
              >
                {content || "…"}
              </ReactMarkdown>
            </div>
          )}
        </div>
        {!isUser && <MetaBadges meta={message.meta} />}
        {!isUser && citations.length > 0 && <Sources citations={citations} />}
        {!isUser && events.length > 0 && <AgentActivity events={events} />}
        {!isUser && question && content && !content.startsWith("⚠️") && content.length > 24 && (
          <EvalButton question={question} answer={content} context={citations.map((c) => c.snippet).join("\n")} />
        )}
        {time && <span className="text-xs text-zinc-400 px-1">{time}</span>}
      </div>
    </div>
  );
}
