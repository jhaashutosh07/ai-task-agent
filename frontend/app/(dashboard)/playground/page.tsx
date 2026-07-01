"use client";

import { useState, useEffect } from "react";
import { Swords, Loader2, Zap, Trophy, AlertCircle, Send } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { getProviderStatus, compareProviders } from "@/lib/api";

const FREE = new Set(["groq", "openrouter", "cerebras", "gemini", "ollama"]);
const COLORS: Record<string, string> = {
  openai: "#10b981", anthropic: "#8b5cf6", gemini: "#3b82f6",
  groq: "#f97316", openrouter: "#ec4899", cerebras: "#06b6d4", ollama: "#f59e0b",
};

interface Result {
  provider: string; model: string; response: string;
  latency_ms: number; error: string | null;
  cost_per_1k?: { input: number; output: number };
}

export default function PlaygroundPage() {
  const [available, setAvailable] = useState<string[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [prompt, setPrompt] = useState("Explain what a vector database is in 2 sentences.");
  const [results, setResults] = useState<Result[]>([]);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    getProviderStatus().then((p) => {
      const names = (p.providers || []).map((x: any) => x.name);
      setAvailable(names);
      setSelected(new Set(names));
    }).catch(() => {});
  }, []);

  const toggle = (n: string) =>
    setSelected((s) => { const c = new Set(s); c.has(n) ? c.delete(n) : c.add(n); return c; });

  const race = async () => {
    if (!prompt.trim() || selected.size === 0 || running) return;
    setRunning(true);
    setResults([]);
    try {
      const r = await compareProviders(prompt, Array.from(selected));
      setResults(r.results || []);
    } catch (e: any) {
      setResults([{ provider: "error", model: "", response: "", latency_ms: 0, error: e.message }]);
    }
    setRunning(false);
  };

  const fastest = results.filter((r) => !r.error).sort((a, b) => a.latency_ms - b.latency_ms)[0]?.provider;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white flex items-center gap-2.5">
          <Swords className="w-6 h-6 text-primary-500" />Model Playground
        </h1>
        <p className="text-zinc-500 dark:text-zinc-400 text-sm mt-1">
          Send one prompt to multiple LLMs at once and compare quality, speed and cost.
        </p>
      </div>

      {/* Prompt + providers */}
      <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-card p-5 space-y-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
          placeholder="Enter a prompt to compare across models…"
          className="w-full resize-none rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 px-4 py-3 text-sm text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:border-primary-400"
        />
        <div className="flex flex-wrap items-center gap-2">
          {available.length === 0 && <span className="text-xs text-zinc-400">Loading providers…</span>}
          {available.map((n) => (
            <button key={n} onClick={() => toggle(n)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                selected.has(n)
                  ? "border-primary-300 bg-primary-50 dark:bg-primary-500/15 text-primary-700 dark:text-primary-300"
                  : "border-zinc-200 dark:border-zinc-700 text-zinc-500"
              }`}>
              <span className="w-2 h-2 rounded-full" style={{ background: COLORS[n] || "#94a3b8" }} />
              <span className="capitalize">{n}</span>
              {FREE.has(n) && <span className="text-[9px] font-bold text-emerald-500">FREE</span>}
            </button>
          ))}
          <button onClick={race} disabled={running || selected.size === 0 || !prompt.trim()}
            className="ml-auto inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-700 disabled:opacity-40 text-white text-sm font-semibold transition-colors">
            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {running ? "Racing…" : "Race models"}
          </button>
        </div>
        {available.length <= 1 && (
          <p className="text-xs text-amber-600 dark:text-amber-400">
            Only one provider is configured. Add a free key (Groq / OpenRouter / Cerebras) to compare more.
          </p>
        )}
      </div>

      {/* Results */}
      {(running || results.length > 0) && (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {running && Array.from(selected).map((n) => (
            <div key={n} className="rounded-2xl border border-zinc-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-card p-5 flex items-center gap-2 text-zinc-400">
              <Loader2 className="w-4 h-4 animate-spin" /> <span className="capitalize text-sm">{n} thinking…</span>
            </div>
          ))}
          {!running && results.map((r) => (
            <div key={r.provider} className={`rounded-2xl border bg-white dark:bg-zinc-900 shadow-card p-5 ${r.provider === fastest ? "border-emerald-300 dark:border-emerald-500/40 ring-1 ring-emerald-200 dark:ring-emerald-500/20" : "border-zinc-100 dark:border-zinc-800"}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[r.provider] || "#94a3b8" }} />
                  <span className="font-semibold text-zinc-900 dark:text-white capitalize">{r.provider}</span>
                  {FREE.has(r.provider) && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-500/15 text-emerald-600">FREE</span>}
                  {r.provider === fastest && <Trophy className="w-3.5 h-3.5 text-amber-500" />}
                </div>
                {!r.error && (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-zinc-500">
                    <Zap className="w-3 h-3" />{(r.latency_ms / 1000).toFixed(2)}s
                  </span>
                )}
              </div>
              {r.model && <p className="text-[11px] text-zinc-400 mb-2 font-mono truncate">{r.model}</p>}
              {r.error ? (
                <div className="flex items-start gap-2 text-xs text-rose-500">
                  <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" /><span>{r.error}</span>
                </div>
              ) : (
                <div className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed max-h-64 overflow-y-auto markdown-content">
                  <ReactMarkdown components={{ p: ({ children }) => <p className="mb-2">{children}</p> }}>
                    {r.response || "_(empty)_"}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
