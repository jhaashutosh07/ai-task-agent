"use client";

import { useState, useRef, useEffect } from "react";
import {
  Sparkles, Send, Loader2, Trash2, FileText,
  Search, Code2, BarChart3, Workflow,
} from "lucide-react";
import { sendMessage, clearChat, getRagStats } from "@/lib/api";
import { useStore } from "@/lib/store";
import MessageBubble from "./MessageBubble";

const SUGGESTIONS = [
  {
    icon: Search,
    title: "Research a topic",
    prompt:
      "Research the latest advances in renewable energy and summarise the top 3 breakthroughs.",
    accent: "from-sky-500 to-blue-600",
  },
  {
    icon: Code2,
    title: "Write some code",
    prompt:
      "Write a Python function that returns the nth Fibonacci number using memoisation, with a short explanation.",
    accent: "from-violet-500 to-purple-600",
  },
  {
    icon: BarChart3,
    title: "Analyse data",
    prompt:
      "I have a CSV of monthly sales. Explain how you'd analyse it and which charts would be most insightful.",
    accent: "from-emerald-500 to-teal-600",
  },
  {
    icon: Workflow,
    title: "Plan a workflow",
    prompt:
      "Draft a step-by-step automation that fetches the day's tech news, summarises it, and emails a digest.",
    accent: "from-amber-500 to-orange-600",
  },
];

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

export default function ChatInterface() {
  const messages = useStore((s) => s.messages);
  const addMessage = useStore((s) => s.addMessage);
  const clearMessages = useStore((s) => s.clearMessages);
  const isLoading = useStore((s) => s.isLoading);
  const setLoading = useStore((s) => s.setLoading);
  const user = useStore((s) => s.user);

  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [docCount, setDocCount] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    getRagStats()
      .then((s) => setDocCount(s?.documents ?? 0))
      .catch(() => {});
  }, []);

  const autosize = () => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
  };

  const send = async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || isLoading) return;

    setInput("");
    setError("");
    if (taRef.current) taRef.current.style.height = "auto";

    addMessage({ role: "user", content: msg });
    setLoading(true);

    try {
      const res = await sendMessage(msg);
      addMessage({
        role: "assistant",
        content:
          res.response?.trim() ||
          "_The agent returned an empty response. Please try rephrasing._",
        events: res.events,
      });
    } catch (e: any) {
      const m = e?.message || "Something went wrong. Please try again.";
      setError(m);
      addMessage({ role: "assistant", content: `⚠️ ${m}` });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    clearMessages();
    setError("");
    try {
      await clearChat();
    } catch {
      /* best-effort server-side clear */
    }
  };

  const isEmpty = messages.length === 0;
  const name = user?.username ? user.username.split(" ")[0] : "there";

  return (
    <div className="flex flex-col h-full bg-[rgb(var(--bg))]">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-zinc-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center shadow-glow">
            <Sparkles className="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-zinc-900 dark:text-white leading-tight">
              Nexus AI
            </h1>
            <p className="text-xs text-zinc-400 leading-tight">
              Multi-agent assistant
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {docCount > 0 && (
            <span
              title={`${docCount} document${docCount > 1 ? "s" : ""} connected to RAG`}
              className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-500/15 border border-emerald-200 dark:border-emerald-500/25 px-2.5 py-1 rounded-lg"
            >
              <FileText className="w-3.5 h-3.5" />
              {docCount} doc{docCount > 1 ? "s" : ""} in context
            </span>
          )}
          {!isEmpty && (
            <button
              onClick={handleClear}
              className="flex items-center gap-1.5 text-xs font-medium text-zinc-500 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 px-2.5 py-1.5 rounded-lg transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Clear</span>
            </button>
          )}
        </div>
      </header>

      {/* ── Messages ───────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        {isEmpty ? (
          <div className="h-full flex flex-col items-center justify-center px-6 py-10 max-w-2xl mx-auto text-center animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center shadow-glow mb-5 float">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-white">
              {greeting()}, <span className="gradient-text">{name}</span>
            </h2>
            <p className="text-zinc-500 dark:text-zinc-400 mt-2 text-sm max-w-md">
              I can research, write and run code, analyse data, and orchestrate
              multi-step tasks across specialised agents. What can I help you
              with?
            </p>

            <div className="grid sm:grid-cols-2 gap-3 mt-8 w-full">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.title}
                  onClick={() => send(s.prompt)}
                  className="group text-left p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:border-primary-300 dark:hover:border-primary-500/40 shadow-card hover:shadow-card-md transition-all"
                >
                  <div
                    className={`w-9 h-9 rounded-xl bg-gradient-to-br ${s.accent} flex items-center justify-center mb-3 group-hover:scale-105 transition-transform`}
                  >
                    <s.icon className="w-4.5 h-4.5 text-white" />
                  </div>
                  <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-100">
                    {s.title}
                  </p>
                  <p className="text-xs text-zinc-400 mt-1 line-clamp-2">
                    {s.prompt}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="px-4 sm:px-6 py-6 max-w-3xl mx-auto flex flex-col gap-5">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}

            {isLoading && (
              <div className="flex gap-3 animate-fade-in">
                <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-card flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-primary-400 pulse-dot" />
                  <span
                    className="w-2 h-2 rounded-full bg-primary-400 pulse-dot"
                    style={{ animationDelay: "0.2s" }}
                  />
                  <span
                    className="w-2 h-2 rounded-full bg-primary-400 pulse-dot"
                    style={{ animationDelay: "0.4s" }}
                  />
                  <span className="text-xs text-zinc-400 ml-1">
                    Agents are working…
                  </span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* ── Composer ───────────────────────────────────────────── */}
      <div className="border-t border-zinc-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-md px-4 sm:px-6 py-4">
        <div className="max-w-3xl mx-auto">
          {error && (
            <p className="text-xs text-rose-500 mb-2 px-1">{error}</p>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
            className="flex items-end gap-2 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-2 glow-focus transition-shadow"
          >
            <textarea
              ref={taRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                autosize();
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Message Nexus AI…  (Shift+Enter for a new line)"
              rows={1}
              className="flex-1 resize-none bg-transparent px-3 py-2 text-sm text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none max-h-44"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="flex-shrink-0 w-10 h-10 rounded-xl bg-primary-600 hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center transition-colors"
              aria-label="Send message"
            >
              {isLoading ? (
                <Loader2 className="w-4.5 h-4.5 animate-spin" />
              ) : (
                <Send className="w-4.5 h-4.5" />
              )}
            </button>
          </form>
          <p className="text-[11px] text-zinc-400 text-center mt-2">
            Nexus AI can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}
