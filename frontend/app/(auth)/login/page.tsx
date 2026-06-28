"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mail, Lock, Eye, EyeOff, Loader2, Sparkles, Zap, Brain, GitBranch } from "lucide-react";
import { login, getCurrentUser, onAuthWaking } from "@/lib/auth";
import { useStore } from "@/lib/store";

const features = [
  { icon: Brain, label: "Multi-agent AI", desc: "Specialized agents work together" },
  { icon: Zap, label: "15+ Tools", desc: "Web, code, files, email & more" },
  { icon: GitBranch, label: "Workflow builder", desc: "Automate complex pipelines" },
  { icon: Sparkles, label: "RAG documents", desc: "Chat with your own files" },
];

export default function LoginPage() {
  const router = useRouter();
  const setUser = useStore((s) => s.setUser);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [waking, setWaking] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    setWaking(false);
    onAuthWaking(() => setWaking(true));
    try {
      await login({ email, password });
      const user = await getCurrentUser();
      if (user) { setUser(user); router.push("/chat"); }
    } catch (err: any) {
      setError(err.message || "Invalid credentials");
    } finally {
      setLoading(false);
      setWaking(false);
      onAuthWaking(null);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* ── Left brand panel ── */}
      <div className="hidden lg:flex lg:w-[52%] auth-gradient relative overflow-hidden flex-col justify-between p-12">
        {/* Decorative blobs */}
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-24 -right-24 w-80 h-80 bg-indigo-400/20 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-violet-500/10 rounded-full blur-2xl" />

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 bg-white/15 backdrop-blur-sm rounded-2xl flex items-center justify-center border border-white/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="text-white font-semibold text-lg tracking-tight">Nexus AI</span>
        </div>

        {/* Hero copy */}
        <div className="relative z-10 space-y-6">
          <div className="space-y-3">
            <p className="text-white/60 text-sm font-medium uppercase tracking-widest">AI-powered workspace</p>
            <h1 className="text-4xl font-bold text-white leading-snug">
              Your intelligent<br />work companion
            </h1>
            <p className="text-white/70 text-lg leading-relaxed max-w-sm">
              Delegate complex tasks to specialized AI agents. Get more done, faster.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {features.map(({ icon: Icon, label, desc }) => (
              <div key={label} className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/10 float">
                <div className="w-8 h-8 bg-white/15 rounded-xl flex items-center justify-center mb-2">
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <p className="text-white font-medium text-sm">{label}</p>
                <p className="text-white/55 text-xs mt-0.5">{desc}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-white/30 text-xs">© 2025 Nexus AI · All rights reserved</p>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-center justify-center p-8 bg-white dark:bg-zinc-950">
        <div className="w-full max-w-sm animate-fade-in">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 bg-primary-600 rounded-xl flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-zinc-900 dark:text-white">Nexus AI</span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-white">Welcome back</h2>
            <p className="text-zinc-500 dark:text-zinc-400 mt-1.5">Sign in to your workspace</p>
          </div>

          {error && (
            <div className="mb-4 px-4 py-3 rounded-xl bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 text-rose-600 dark:text-rose-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Email</label>
              <div className="relative glow-focus rounded-xl">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:border-primary-500 dark:focus:border-primary-500 transition-colors text-sm"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Password</label>
                <a href="#" className="text-xs text-primary-600 dark:text-primary-400 hover:underline">Forgot password?</a>
              </div>
              <div className="relative glow-focus rounded-xl">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} required
                  placeholder="Your password"
                  className="w-full pl-10 pr-10 py-3 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:border-primary-500 dark:focus:border-primary-500 transition-colors text-sm"
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full py-3 rounded-xl bg-primary-600 hover:bg-primary-700 disabled:opacity-60 text-white font-medium text-sm transition-all flex items-center justify-center gap-2 shadow-glow mt-2"
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" />{waking ? "Waking up server…" : "Signing in…"}</> : "Sign in"}
            </button>

            {waking && (
              <p className="text-xs text-zinc-400 text-center -mt-1">
                The free-tier server was asleep — first sign-in can take up to a minute. Hang tight, it'll log you in automatically.
              </p>
            )}
          </form>

          <p className="mt-6 text-center text-sm text-zinc-500 dark:text-zinc-400">
            No account yet?{" "}
            <Link href="/register" className="text-primary-600 dark:text-primary-400 font-medium hover:underline">
              Create one free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}