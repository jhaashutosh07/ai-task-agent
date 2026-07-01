"use client";

import { useState, useRef, useEffect } from "react";
import {
  Sparkles, Send, Loader2, Trash2, FileText,
  Search, Code2, BarChart3, Workflow, Zap,
  Mic, MicOff, Volume2, VolumeX,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { streamChat, clearChat, getRagStats } from "@/lib/api";
import { useStore } from "@/lib/store";
import { AgentEvent, Citation, ChatMeta } from "@/lib/types";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import MessageBubble from "./MessageBubble";
import AgentGraph from "./AgentGraph";

// Strip markdown/emoji so text-to-speech reads cleanly.
function forSpeech(md: string): string {
  return md
    .replace(/```[\s\S]*?```/g, " code block ")
    .replace(/[#*_`>\[\]()]/g, "")
    .replace(/⚠️/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

const SUGGESTIONS = [
  { icon: Search, title: "Research a topic", prompt: "Research the latest advances in renewable energy and summarise the top 3 breakthroughs.", accent: "from-sky-500 to-blue-600" },
  { icon: Code2, title: "Write some code", prompt: "Write a Python function that returns the nth Fibonacci number using memoisation, with a short explanation.", accent: "from-violet-500 to-purple-600" },
  { icon: BarChart3, title: "Analyse data", prompt: "I have a CSV of monthly sales. Explain how you'd analyse it and which charts would be most insightful.", accent: "from-emerald-500 to-teal-600" },
  { icon: Workflow, title: "Plan a workflow", prompt: "Draft a step-by-step automation that fetches the day's tech news, summarises it, and emails a digest.", accent: "from-amber-500 to-orange-600" },
];

const STAGE_LABELS: Record<string, string> = {
  classified: "Routing your request",
  cache_hit: "Found a cached answer",
  retrieved: "Reading your documents",
  generating: "Generating a response",
  orchestrating: "Coordinating agents",
  responding: "Composing the answer",
};

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

interface StreamState {
  active: boolean;
  content: string;
  stage: string;
  steps: AgentEvent[];
  citations: Citation[];
  meta: ChatMeta;
}

const EMPTY_STREAM: StreamState = {
  active: false, content: "", stage: "", steps: [], citations: [], meta: {},
};

export default function ChatInterface() {
  const messages = useStore((s) => s.messages);
  const addMessage = useStore((s) => s.addMessage);
  const clearMessages = useStore((s) => s.clearMessages);
  const user = useStore((s) => s.user);

  const [input, setInput] = useState("");
  const [stream, setStream] = useState<StreamState>(EMPTY_STREAM);
  const [docCount, setDocCount] = useState(0);
  const [voiceOut, setVoiceOut] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const voiceOutRef = useRef(false);
  useEffect(() => { voiceOutRef.current = voiceOut; }, [voiceOut]);

  const { isListening, isSupported: micSupported, startListening, stopListening } =
    useSpeechRecognition({
      onResult: (transcript, isFinal) => {
        if (isFinal) setInput((p) => (p ? p.trim() + " " : "") + transcript);
      },
    });
  const { speak, cancel: cancelSpeech, isSupported: ttsSupported } = useSpeechSynthesis();

  const isLoading = stream.active;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, stream]);

  useEffect(() => {
    getRagStats().then((s) => setDocCount(s?.documents ?? 0)).catch(() => {});
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
    if (taRef.current) taRef.current.style.height = "auto";

    addMessage({ role: "user", content: msg });
    setStream({ ...EMPTY_STREAM, active: true, stage: "classified" });

    // Local accumulators (state updates are async / batched).
    let content = "";
    let steps: AgentEvent[] = [];
    let citations: Citation[] = [];
    let meta: ChatMeta = {};

    try {
      await streamChat(msg, {
        onMeta: (m) => { meta = { ...meta, ...m }; setStream((s) => ({ ...s, meta })); },
        onStage: (st) => setStream((s) => ({ ...s, stage: st.name })),
        onStep: (e) => { steps = [...steps, e]; setStream((s) => ({ ...s, steps })); },
        onToken: (t) => { content += t; setStream((s) => ({ ...s, content })); },
        onCitations: (c) => { citations = c; setStream((s) => ({ ...s, citations })); },
        onDone: (d) => {
          const finalContent = (content || d.response || "").trim();
          addMessage({
            role: "assistant",
            content: finalContent || "_(empty response)_",
            events: steps,
            citations: d.citations?.length ? d.citations : citations,
            meta: { ...meta, latency_ms: d.latency_ms },
          });
          if (voiceOutRef.current && finalContent) speak(forSpeech(finalContent));
          setStream(EMPTY_STREAM);
        },
        onError: (m) => {
          addMessage({ role: "assistant", content: `⚠️ ${m}`, meta });
          setStream(EMPTY_STREAM);
        },
      });
    } catch (e: any) {
      addMessage({ role: "assistant", content: `⚠️ ${e?.message || "Stream failed"}` });
      setStream(EMPTY_STREAM);
    }
  };

  const handleClear = async () => {
    clearMessages();
    setStream(EMPTY_STREAM);
    try { await clearChat(); } catch { /* best-effort */ }
  };

  const isEmpty = messages.length === 0 && !stream.active;
  const name = user?.username ? user.username.split(" ")[0] : "there";

  return (
    <div className="flex flex-col h-full bg-[rgb(var(--bg))]">
      {/* Header */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-zinc-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center shadow-glow">
            <Sparkles className="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-zinc-900 dark:text-white leading-tight">Nexus AI</h1>
            <p className="text-xs text-zinc-400 leading-tight">Streaming · multi-agent · RAG</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {docCount > 0 && (
            <span title={`${docCount} document(s) connected to RAG`} className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-500/15 border border-emerald-200 dark:border-emerald-500/25 px-2.5 py-1 rounded-lg">
              <FileText className="w-3.5 h-3.5" />{docCount} doc{docCount > 1 ? "s" : ""} in context
            </span>
          )}
          {ttsSupported && (
            <button
              onClick={() => { setVoiceOut((v) => { if (v) cancelSpeech(); return !v; }); }}
              title={voiceOut ? "Voice replies on" : "Voice replies off"}
              className={`p-1.5 rounded-lg transition-colors ${voiceOut ? "text-primary-600 bg-primary-50 dark:bg-primary-500/15" : "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"}`}
            >
              {voiceOut ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>
          )}
          {messages.length > 0 && (
            <button onClick={handleClear} className="flex items-center gap-1.5 text-xs font-medium text-zinc-500 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 px-2.5 py-1.5 rounded-lg transition-colors">
              <Trash2 className="w-3.5 h-3.5" /><span className="hidden sm:inline">Clear</span>
            </button>
          )}
        </div>
      </header>

      {/* Messages */}
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
              I route simple questions to a fast conversational model and complex tasks to a team of
              specialised agents — with retrieval, citations, and live reasoning.
            </p>
            <div className="grid sm:grid-cols-2 gap-3 mt-8 w-full">
              {SUGGESTIONS.map((s) => (
                <button key={s.title} onClick={() => send(s.prompt)} className="group text-left p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:border-primary-300 dark:hover:border-primary-500/40 shadow-card hover:shadow-card-md transition-all">
                  <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${s.accent} flex items-center justify-center mb-3 group-hover:scale-105 transition-transform`}>
                    <s.icon className="w-4.5 h-4.5 text-white" />
                  </div>
                  <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-100">{s.title}</p>
                  <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{s.prompt}</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="px-4 sm:px-6 py-6 max-w-3xl mx-auto flex flex-col gap-5">
            {messages.map((m) => <MessageBubble key={m.id} message={m} />)}

            {/* Live streaming bubble */}
            {stream.active && (
              <div className="flex gap-3 animate-fade-in">
                <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div className="max-w-[78%] flex flex-col gap-1 items-start">
                  <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-card text-sm leading-relaxed text-zinc-800 dark:text-zinc-100 min-w-[120px]">
                    {stream.content ? (
                      <div className="markdown-content space-y-2">
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                            code: ({ children }) => <code className="bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>,
                          }}
                        >
                          {stream.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-zinc-500">
                        {stream.meta.cache_hit ? <Zap className="w-3.5 h-3.5 text-amber-500" /> : <Loader2 className="w-3.5 h-3.5 animate-spin text-primary-500" />}
                        <span className="text-xs">{STAGE_LABELS[stream.stage] || "Thinking"}…</span>
                      </div>
                    )}
                  </div>

                  {/* Live multi-agent reasoning graph (task path) */}
                  {stream.steps.length > 0 && (
                    <div className="w-full max-w-md mt-1">
                      <AgentGraph events={stream.steps} />
                    </div>
                  )}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Composer */}
      <div className="border-t border-zinc-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-md px-4 sm:px-6 py-4">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={(e) => { e.preventDefault(); send(); }} className="flex items-end gap-2 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-2 glow-focus transition-shadow">
            {micSupported && (
              <button
                type="button"
                onClick={() => (isListening ? stopListening() : startListening())}
                title={isListening ? "Stop listening" : "Speak your message"}
                className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
                  isListening
                    ? "bg-rose-500 text-white shadow-glow"
                    : "text-zinc-500 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-500/10"
                }`}
              >
                {isListening ? <MicOff className="w-4.5 h-4.5" /> : <Mic className="w-4.5 h-4.5" />}
              </button>
            )}
            <textarea
              ref={taRef}
              value={input}
              onChange={(e) => { setInput(e.target.value); autosize(); }}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
              placeholder={isListening ? "Listening… speak now" : "Message Nexus AI…  (Shift+Enter for a new line)"}
              rows={1}
              className="flex-1 resize-none bg-transparent px-3 py-2 text-sm text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none max-h-44"
            />
            <button type="submit" disabled={!input.trim() || isLoading} className="flex-shrink-0 w-10 h-10 rounded-xl bg-primary-600 hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center transition-colors" aria-label="Send message">
              {isLoading ? <Loader2 className="w-4.5 h-4.5 animate-spin" /> : <Send className="w-4.5 h-4.5" />}
            </button>
          </form>
          <p className="text-[11px] text-zinc-400 text-center mt-2">
            Nexus AI streams responses and can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}
