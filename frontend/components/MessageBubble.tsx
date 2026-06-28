"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { User, Sparkles, ChevronDown, Wrench, Check, X } from "lucide-react";
import { Message, AgentEvent } from "@/lib/types";
import CodeBlock from "./CodeBlock";

function AgentActivity({ events }: { events: AgentEvent[] }) {
  const [open, setOpen] = useState(false);
  // Keep only meaningful agent/tool steps for a readable trail.
  const steps = events.filter(
    (e) => e.type === "tool_call" || e.type === "tool_result" || e.type === "agent_start" || e.type === "agent_delegate"
  );
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
          {steps.map((e, i) => {
            const label = e.data.tool || e.agent || e.data.description || e.type;
            const ok = e.data.success;
            return (
              <div key={i} className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
                {ok === true && <Check className="w-3 h-3 text-emerald-500 flex-shrink-0" />}
                {ok === false && <X className="w-3 h-3 text-rose-500 flex-shrink-0" />}
                {ok === undefined && <span className="w-1.5 h-1.5 rounded-full bg-primary-400 flex-shrink-0" />}
                <span className="font-mono truncate">{label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const content = message.content || "";
  const events = message.events || [];
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
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>
        {!isUser && events.length > 0 && <AgentActivity events={events} />}
        {time && <span className="text-xs text-zinc-400 px-1">{time}</span>}
      </div>
    </div>
  );
}