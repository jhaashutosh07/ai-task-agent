"use client";

import Link from "next/link";
import {
  Sparkles, ArrowRight, Github, Search, Code2, FileText, Database,
  GitBranch, Brain, ShieldCheck, Gauge, Check, CornerDownLeft,
} from "lucide-react";

/* ── Small building blocks ───────────────────────────────────────────── */

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-600 dark:text-primary-400">
      {children}
    </span>
  );
}

/* A miniature, static replica of the chat UI — gives the hero a real product feel. */
function ProductPreview() {
  return (
    <div className="relative">
      <div className="absolute -inset-4 bg-gradient-to-tr from-primary-500/20 to-violet-500/10 blur-2xl rounded-[2rem] -z-10" />
      <div className="rounded-2xl border border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-card-lg overflow-hidden">
        <div className="flex items-center gap-1.5 px-4 h-9 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-950/40">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-400/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/70" />
          <span className="ml-2 text-[11px] text-zinc-400">nexus — chat</span>
        </div>
        <div className="p-4 space-y-3 text-sm">
          <div className="flex justify-end">
            <div className="bg-primary-600 text-white rounded-2xl rounded-tr-sm px-3.5 py-2 max-w-[80%]">
              Research the top 3 AI breakthroughs and write a short summary.
            </div>
          </div>
          <div className="flex gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="flex-1 space-y-2">
              <div className="rounded-2xl rounded-tl-sm border border-zinc-100 dark:border-zinc-800 px-3.5 py-2.5">
                <div className="flex items-center gap-2 text-[11px] text-zinc-400 mb-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-400 pulse-dot" /> Orchestrator delegating…
                </div>
                <div className="grid grid-cols-4 gap-1.5">
                  {[
                    { l: "Research", on: true },
                    { l: "Coder", on: false },
                    { l: "Analyst", on: true },
                    { l: "Exec", on: false },
                  ].map((a) => (
                    <div key={a.l} className={`text-[10px] text-center rounded-lg py-1.5 border ${a.on ? "border-primary-300 bg-primary-50 dark:bg-primary-500/15 text-primary-600 dark:text-primary-300" : "border-zinc-200 dark:border-zinc-700 text-zinc-400"}`}>
                      {a.l}
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl rounded-tl-sm border border-zinc-100 dark:border-zinc-800 px-3.5 py-2.5 text-zinc-600 dark:text-zinc-300 text-[13px] leading-relaxed">
                Here are the three most significant breakthroughs, grounded in your sources&nbsp;
                <span className="text-primary-500 font-medium">[1]</span>…
                <div className="mt-2 flex gap-1.5">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-500/10 text-amber-600">cached</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600">★ 4.7/5</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Architecture flow (beginner-friendly) ───────────────────────────── */

const PIPELINE = [
  { icon: Database, title: "Cache", plain: "Seen a similar question? Answer instantly." },
  { icon: GitBranch, title: "Router", plain: "Quick chat, or a complex multi-step task?" },
  { icon: Search, title: "Retrieve", plain: "Pull the relevant bits from your documents." },
  { icon: Brain, title: "Agents", plain: "A lead agent delegates to specialists." },
  { icon: ShieldCheck, title: "Reflect", plain: "Double-check the answer before replying." },
];

function ArchitectureFlow() {
  return (
    <div className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 sm:p-10 shadow-card">
      {/* Layer 1 — you */}
      <div className="flex flex-col items-center">
        <div className="px-4 py-2 rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-sm font-semibold">
          You · in the browser
        </div>
        <p className="text-xs text-zinc-400 mt-1">ask a question, upload a doc, or speak</p>
        <div className="my-3 h-6 w-px bg-gradient-to-b from-zinc-300 to-transparent dark:from-zinc-600" />
      </div>

      {/* Layer 2 — frontend */}
      <div className="flex flex-col items-center">
        <div className="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-sm font-medium">
          Frontend · Next.js
        </div>
        <p className="text-xs text-zinc-400 mt-1">streams the request over a live connection</p>
        <div className="my-3 h-6 w-px bg-gradient-to-b from-zinc-300 to-transparent dark:from-zinc-600" />
      </div>

      {/* Layer 3 — the pipeline */}
      <div className="rounded-2xl border-2 border-dashed border-primary-200 dark:border-primary-500/30 bg-primary-50/40 dark:bg-primary-500/5 p-5">
        <p className="text-center text-xs font-semibold uppercase tracking-wider text-primary-600 dark:text-primary-400 mb-4">
          Backend brain · every request flows through this pipeline
        </p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {PIPELINE.map((s, i) => (
            <div key={s.title} className="relative">
              <div className="h-full rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 p-3.5 text-center">
                <div className="w-9 h-9 mx-auto rounded-lg bg-primary-100 dark:bg-primary-500/15 flex items-center justify-center mb-2">
                  <s.icon className="w-4.5 h-4.5 text-primary-600 dark:text-primary-400" />
                </div>
                <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-100">{i + 1}. {s.title}</p>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1 leading-snug">{s.plain}</p>
              </div>
              {i < PIPELINE.length - 1 && (
                <ArrowRight className="hidden md:block absolute top-1/2 -right-2.5 -translate-y-1/2 w-4 h-4 text-primary-300 dark:text-primary-500/50 z-10" />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="my-3 flex justify-center"><div className="h-6 w-px bg-gradient-to-b from-transparent via-zinc-300 to-zinc-300 dark:via-zinc-600 dark:to-zinc-600" /></div>

      {/* Layer 4 — data + models */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { icon: Brain, t: "8 LLM providers", s: "OpenAI · Groq · Ollama…" },
          { icon: Database, t: "PostgreSQL", s: "accounts + documents" },
          { icon: FileText, t: "Vector store", s: "semantic search" },
        ].map((d) => (
          <div key={d.t} className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/50 p-3 text-center">
            <d.icon className="w-4.5 h-4.5 mx-auto text-zinc-500 mb-1.5" />
            <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-200">{d.t}</p>
            <p className="text-[10px] text-zinc-400">{d.s}</p>
          </div>
        ))}
      </div>

      <div className="mt-5 flex items-center justify-center gap-2 text-sm text-zinc-500 dark:text-zinc-400">
        <CornerDownLeft className="w-4 h-4 text-emerald-500" />
        the answer streams back to you — word by word, with sources & a quality score
      </div>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────────────────── */

const PROVIDERS = ["OpenAI", "Anthropic", "Gemini", "Groq", "OpenRouter", "Cerebras", "Ollama"];

const FEATURES = [
  { icon: Brain, title: "A team of agents", desc: "A lead agent breaks work down and hands it to research, coding, analysis and execution specialists." },
  { icon: FileText, title: "Answers from your docs", desc: "Upload files and get responses grounded in them — with inline citations you can trust." },
  { icon: Gauge, title: "Fast and frugal", desc: "A semantic cache and smart routing keep responses quick and costs near zero." },
  { icon: ShieldCheck, title: "Checked & guarded", desc: "Every answer can be graded by an LLM judge, with PII and prompt-injection guardrails." },
];

const STEPS = [
  { n: "01", t: "Ask anything", d: "Type, talk, or drop in an image or document. Simple questions and hard multi-step tasks both welcome." },
  { n: "02", t: "Watch it think", d: "See the agents light up in real time as they research, write code, and reason — nothing hidden." },
  { n: "03", t: "Get a grounded answer", d: "Streamed word-by-word with citations, a quality score, and full cost/latency tracing." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-[rgb(var(--bg))] text-[rgb(var(--fg))] antialiased">
      {/* Nav */}
      <nav className="sticky top-0 z-40 backdrop-blur-md bg-white/70 dark:bg-zinc-950/70 border-b border-zinc-200/60 dark:border-zinc-800/60">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center">
              <Sparkles className="w-4.5 h-4.5 text-white" />
            </div>
            <span className="font-semibold tracking-tight">Nexus AI</span>
          </div>
          <div className="flex items-center gap-1">
            <a href="#how" className="hidden sm:block px-3 py-2 text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors">How it works</a>
            <a href="#architecture" className="hidden sm:block px-3 py-2 text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors">Architecture</a>
            <Link href="/login" className="px-3 py-2 text-sm text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition-colors">Sign in</Link>
            <Link href="/register" className="ml-1 px-4 py-2 text-sm font-medium rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90 transition-opacity">Start free</Link>
          </div>
        </div>
      </nav>

      {/* Hero — two column, asymmetric */}
      <section className="max-w-5xl mx-auto px-6 pt-16 pb-20 grid lg:grid-cols-[1.05fr_1fr] gap-12 items-center">
        <div>
          <Eyebrow>Multi-agent AI workspace</Eyebrow>
          <h1 className="mt-4 text-4xl sm:text-5xl font-bold tracking-tight leading-[1.08]">
            Delegate the hard stuff to a team of AI agents.
          </h1>
          <p className="mt-5 text-lg text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-lg">
            Nexus researches, writes code, reads your documents and reasons through
            multi-step tasks — streaming its thinking live, and grounding every answer
            in real sources.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link href="/register" className="group inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-primary-600 hover:bg-primary-700 text-white font-medium transition-colors">
              Start for free <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <a href="https://github.com/jhaashutosh07/ai-task-agent" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 px-5 py-3 rounded-xl border border-zinc-200 dark:border-zinc-800 font-medium hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-colors">
              <Github className="w-4 h-4" /> Read the code
            </a>
          </div>
          <div className="mt-7 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-zinc-500">
            {["No credit card", "8 LLM providers", "Open source"].map((t) => (
              <span key={t} className="inline-flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-emerald-500" />{t}</span>
            ))}
          </div>
        </div>
        <ProductPreview />
      </section>

      {/* Providers strip */}
      <section className="border-y border-zinc-100 dark:border-zinc-800/60 bg-zinc-50/50 dark:bg-zinc-950/30">
        <div className="max-w-5xl mx-auto px-6 py-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          <span className="text-xs text-zinc-400">Runs on your choice of</span>
          {PROVIDERS.map((p) => (
            <span key={p} className="text-sm font-medium text-zinc-500 dark:text-zinc-400">{p}</span>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="max-w-5xl mx-auto px-6 py-20">
        <div className="max-w-xl">
          <Eyebrow>How it works</Eyebrow>
          <h2 className="mt-3 text-3xl font-bold tracking-tight">Three steps, no black box.</h2>
        </div>
        <div className="mt-10 grid md:grid-cols-3 gap-6">
          {STEPS.map((s) => (
            <div key={s.n} className="relative">
              <span className="text-5xl font-bold text-zinc-100 dark:text-zinc-800 select-none">{s.n}</span>
              <h3 className="text-lg font-semibold -mt-4">{s.t}</h3>
              <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="max-w-5xl mx-auto px-6 py-16">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <Eyebrow>Under the hood</Eyebrow>
          <h2 className="mt-3 text-3xl font-bold tracking-tight">What actually happens when you hit send</h2>
          <p className="mt-3 text-zinc-500 dark:text-zinc-400">
            New to this? Here&apos;s the whole journey of a single message — in plain English.
          </p>
        </div>
        <ArchitectureFlow />
      </section>

      {/* Features — asymmetric bento */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-2 gap-5">
          {FEATURES.map((f, i) => (
            <div key={f.title} className={`rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6 hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors ${i === 0 ? "bg-gradient-to-br from-primary-50/60 to-transparent dark:from-primary-500/5" : "bg-white dark:bg-zinc-900"}`}>
              <div className="w-10 h-10 rounded-xl bg-zinc-900 dark:bg-white flex items-center justify-center mb-4">
                <f.icon className="w-5 h-5 text-white dark:text-zinc-900" />
              </div>
              <h3 className="text-lg font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="rounded-3xl bg-zinc-900 dark:bg-zinc-900 border border-zinc-800 p-10 sm:p-14 text-center relative overflow-hidden">
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary-500/20 blur-3xl rounded-full" />
          <h2 className="relative text-3xl font-bold text-white tracking-tight">See it think for yourself.</h2>
          <p className="relative text-zinc-400 mt-3 max-w-md mx-auto">Free account, no card. Sign in and watch a team of agents get to work.</p>
          <Link href="/register" className="relative inline-flex items-center gap-2 mt-7 px-6 py-3 rounded-xl bg-white text-zinc-900 font-medium hover:opacity-90 transition-opacity">
            Get started <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-zinc-100 dark:border-zinc-800/60">
        <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-zinc-400">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary-500" /> Nexus AI
          </div>
          <span>Built as a multi-agent AI engineering project · © 2025</span>
        </div>
      </footer>
    </div>
  );
}
