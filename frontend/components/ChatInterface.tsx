"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Trash2, Loader2, Sparkles, ArrowDown } from "lucide-react";
import { useStore } from "@/lib/store";
import { sendMessage, clearChat } from "@/lib/api";
import MessageBubble from "./MessageBubble";
import TaskProgress from "./TaskProgress";
import VoiceInput from "./VoiceInput";

const SUGGESTIONS = [
  "Search for the latest AI research papers",
  "Write a Python script to parse a CSV",
  "What can you help me with?",
  "Summarize a topic and save it to a file",
];

export default function ChatInterface() {
  const [input, setInput] = useState("");
  const [showScroll, setShowScroll] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { messages, addMessage, clearMessages, isLoading, setLoading, currentEvents, addEvent, clearEvents } = useStore();

  const scrollToBottom = () => bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    setShowScroll(el.scrollHeight - el.scrollTop - el.clientHeight > 120);
  };

  const handleVoiceTranscript = (text: string) => setInput(p => p ? `${p} ${text}` : text);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const msg = input.trim();
    setInput("");
    clearEvents();
    addMessage({ role: "user", content: msg });
    setLoading(true);
    try {
      const res = await sendMessage(msg);
      res.events?.forEach(addEvent);
      addMessage({ role: "assistant", content: res.response, events: res.events });
    } catch (err) {
      addMessage({ role: "assistant", content: `Sorry, something went wrong: ${err instanceof Error ? err.message : "Unknown error"}` });
    } finally {
      setLoading(false);
      clearEvents();
    }
  };

  const handleClear = async () => {
    try { await clearChat(); } catch {}
    clearMessages();
    clearEvents();
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(e); }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-50 dark:bg-zinc-950">
      {/* Header */}
      <div className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-5 py-3.5 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-violet-600 rounded-xl flex items-center justify-center shadow-glow">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-zinc-900 dark:text-white text-sm">Nexus AI</h1>
            <p className="text-xs text-zinc-400 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-dot" />
              {isLoading ? "Thinking…" : "Ready to help"}
            </p>
          </div>
        </div>
        <button onClick={handleClear} title="Clear conversation"
          className="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl text-zinc-400 hover:text-rose-500 transition-colors">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} onScroll={handleScroll} className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-16 animate-fade-in">
            <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-violet-600 rounded-2xl flex items-center justify-center mb-5 shadow-glow">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-xl font-bold text-zinc-900 dark:text-white mb-2">What shall we work on?</h2>
            <p className="text-zinc-500 dark:text-zinc-400 text-sm max-w-xs leading-relaxed mb-6">
              I can search the web, run code, manage files, and coordinate multiple AI agents to get things done.
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-md">
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => setInput(s)}
                  className="px-3.5 py-2 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm text-zinc-600 dark:text-zinc-300 hover:border-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors shadow-card">
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map(m => <MessageBubble key={m.id} message={m} />)}

            {isLoading && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center shadow-glow">
                  <Sparkles className="w-4 h-4 text-white animate-spin-slow" />
                </div>
                <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl rounded-tl-sm shadow-card p-4 max-w-[78%]">
                  {currentEvents.length > 0
                    ? <TaskProgress events={currentEvents} />
                    : <div className="flex items-center gap-2 text-zinc-500 text-sm"><Loader2 className="w-4 h-4 animate-spin" />Thinking…</div>
                  }
                </div>
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Scroll button */}
      {showScroll && (
        <button onClick={scrollToBottom}
          className="absolute bottom-24 right-6 w-8 h-8 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-full flex items-center justify-center shadow-card-md text-zinc-500 hover:text-zinc-700 transition-all">
          <ArrowDown className="w-4 h-4" />
        </button>
      )}

      {/* Input */}
      <div className="bg-white dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800 p-4 flex-shrink-0">
        <form onSubmit={handleSubmit}
          className="flex items-end gap-2 bg-zinc-50 dark:bg-zinc-800 rounded-2xl border border-zinc-200 dark:border-zinc-700 px-3 py-2 focus-within:border-primary-400 transition-colors shadow-card">
          <VoiceInput onTranscript={handleVoiceTranscript} disabled={isLoading}
            className="p-2 rounded-xl flex-shrink-0 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300" />
          <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={onKey}
            placeholder="Message Nexus AI…" rows={1}
            className="flex-1 bg-transparent resize-none text-sm text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none py-1.5 max-h-36 leading-relaxed" />
          <button type="submit" disabled={!input.trim() || isLoading}
            className="p-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-40 text-white rounded-xl transition-all flex-shrink-0">
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </form>
        <p className="text-center text-xs text-zinc-400 mt-2">Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}