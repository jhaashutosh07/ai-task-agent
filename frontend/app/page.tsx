"use client";

import Link from "next/link";
import {
  Sparkles, ArrowRight, Brain, FileText, Zap, GitBranch, Mic,
  BarChart3, Workflow, Github, Search, Code2, Database, Gauge, Shield,
} from "lucide-react";

const FEATURES = [
  { icon: Brain, title: "Multi-Agent Orchestration", desc: "An orchestrator decomposes tasks and delegates to specialised researcher, coder, analyst & executor agents.", accent: "from-violet-500 to-purple-600" },
  { icon: FileText, title: "RAG with Citations", desc: "Upload documents → hybrid retrieval + reranking → answers grounded in your sources with inline [n] citations.", accent: "from-sky-500 to-blue-600" },
  { icon: Zap, title: "Real-Time Streaming", desc: "Server-Sent Events stream tokens and live agent steps as the system reasons through your request.", accent: "from-amber-500 to-orange-600" },
  { icon: Gauge, title: "Semantic Cache", desc: "Embedding-similarity response cache cuts latency and cost on repeated or paraphrased questions.", accent: "from-emerald-500 to-teal-600" },
  { icon: BarChart3, title: "Observability", desc: "Built-in request tracing plus a live dashboard: latency p95, cache-hit rate, cost & intent mix.", accent: "from-rose-500 to-pink-600" },
  { icon: Mic, title: "Voice Mode", desc: "Talk to the assistant and hear it reply — hands-free, right in the browser.", accent: "from-cyan-500 to-blue-600" },
];

const PROVIDERS = ["OpenAI", "Anthropic", "Gemini", "Groq", "OpenRouter", "Cerebras", "Ollama"];
const STACK = ["FastAPI", "Next.js 14", "PostgreSQL", "ChromaDB", "Docker", "TypeScript"];

export default function Landing() {
  return (
    <div className="min-h-screen bg-[rgb(var(--bg))] text-[rgb(var(--fg))] overflow-x-hidden">
      {/* Nav */}
      <nav className="sticky top-0 z-40 backdrop-blur-md bg-white/70 dark:bg-zinc-950/70 border-b border-zinc-200/60 dark:border-zinc-800/60">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center shadow-glow">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg">Nexus AI</span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/login" className="px-4 py-2 text-sm font-medium text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition-colors">Sign in</Link>
            <Link href="/register" className="px-4 py-2 text-sm font-semibold rounded-xl bg-primary-600 hover:bg-primary-700 text-white shadow-glow transition-colors">Get started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative max-w-6xl mx-auto px-6 pt-20 pb-24 text-center">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[40rem] h-[40rem] bg-primary-500/10 rounded-full blur-3xl -z-10" />
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-50 dark:bg-primary-500/10 border border-primary-200 dark:border-primary-500/20 text-primary-600 dark:text-primary-400 text-xs font-medium mb-6 animate-fade-in">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-dot" />
          Multi-agent · RAG · Streaming · 7 LLM providers
        </div>
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-[1.05] animate-fade-in">
          Your intelligent<br /><span className="gradient-text">multi-agent workspace</span>
        </h1>
        <p className="max-w-2xl mx-auto mt-6 text-lg text-zinc-500 dark:text-zinc-400 leading-relaxed animate-fade-in">
          Nexus AI decomposes complex tasks across specialised agents, grounds answers in your
          documents with citations, and streams its reasoning live — with built-in cost tracking,
          caching, and observability.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 mt-8 animate-slide-up">
          <Link href="/register" className="group inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary-600 hover:bg-primary-700 text-white font-semibold shadow-glow transition-all">
            Try it free <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <a href="https://github.com/jhaashutosh07/ai-task-agent" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 font-semibold shadow-card hover:shadow-card-md transition-all">
            <Github className="w-4 h-4" /> View source
          </a>
        </div>

        {/* Provider marquee */}
        <div className="mt-14">
          <p className="text-xs uppercase tracking-widest text-zinc-400 mb-4">Works with</p>
          <div className="flex flex-wrap items-center justify-center gap-2.5">
            {PROVIDERS.map((p) => (
              <span key={p} className="px-3 py-1.5 rounded-lg bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-sm font-medium text-zinc-600 dark:text-zinc-300 shadow-card">{p}</span>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">Not just a chatbot</h2>
          <p className="text-zinc-500 dark:text-zinc-400 mt-2">A production-grade agentic platform, end to end.</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f) => (
            <div key={f.title} className="group p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-card hover:shadow-card-lg transition-all">
              <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${f.accent} flex items-center justify-center mb-4 group-hover:scale-105 transition-transform`}>
                <f.icon className="w-5.5 h-5.5 text-white" />
              </div>
              <h3 className="font-semibold text-lg">{f.title}</h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1.5 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pipeline */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="rounded-3xl bg-gradient-to-br from-zinc-900 to-zinc-800 dark:from-zinc-900 dark:to-black p-8 sm:p-12 text-white shadow-card-lg">
          <h2 className="text-2xl font-bold text-center mb-2">The intelligent pipeline</h2>
          <p className="text-zinc-400 text-center text-sm mb-10">Every message takes the cheapest correct path.</p>
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
            {[
              { icon: Database, label: "Semantic Cache" },
              { icon: GitBranch, label: "Intent Router" },
              { icon: Search, label: "RAG Retrieval" },
              { icon: Brain, label: "Agent Orchestration" },
              { icon: Shield, label: "Self-Reflection" },
              { icon: Gauge, label: "Trace & Metrics" },
            ].map((s, i, arr) => (
              <div key={s.label} className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/10">
                  <s.icon className="w-4 h-4 text-primary-300" />
                  <span className="font-medium">{s.label}</span>
                </div>
                {i < arr.length - 1 && <ArrowRight className="w-4 h-4 text-zinc-600 hidden sm:block" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stack + CTA */}
      <section className="max-w-6xl mx-auto px-6 py-16 text-center">
        <p className="text-xs uppercase tracking-widest text-zinc-400 mb-4">Built with</p>
        <div className="flex flex-wrap items-center justify-center gap-2.5 mb-16">
          {STACK.map((s) => (
            <span key={s} className="px-3 py-1.5 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-sm font-medium text-zinc-600 dark:text-zinc-300">{s}</span>
          ))}
        </div>
        <div className="rounded-3xl auth-gradient p-12 text-white relative overflow-hidden">
          <div className="absolute -top-16 -right-16 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
          <h2 className="text-3xl font-bold relative">Ready to explore?</h2>
          <p className="text-white/80 mt-2 relative">Create a free account and start delegating to your AI workforce.</p>
          <Link href="/register" className="relative inline-flex items-center gap-2 mt-6 px-6 py-3 rounded-xl bg-white text-primary-700 font-semibold shadow-lg hover:scale-[1.02] transition-transform">
            Get started free <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-8 text-center text-sm text-zinc-400">
        Nexus AI — a multi-agent AI platform. © 2025
      </footer>
    </div>
  );
}
