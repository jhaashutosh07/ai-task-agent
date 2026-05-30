"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mail, Lock, User, Eye, EyeOff, Loader2, Sparkles, CheckCircle2 } from "lucide-react";
import { register, login, getCurrentUser } from "@/lib/auth";
import { useStore } from "@/lib/store";

export default function RegisterPage() {
  const router = useRouter();
  const setUser = useStore((s) => s.setUser);
  const [form, setForm] = useState({ username: "", email: "", password: "", confirm: "" });
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const reqs = [
    { ok: form.password.length >= 8, text: "At least 8 characters" },
    { ok: /[A-Z]/.test(form.password), text: "One uppercase letter" },
    { ok: /[0-9]/.test(form.password), text: "One number" },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) return setError("Passwords do not match");
    setLoading(true);
    try {
      await register({ email: form.email, username: form.username, password: form.password });
      await login({ email: form.email, password: form.password });
      const user = await getCurrentUser();
      if (user) { setUser(user); router.push("/chat"); }
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally { setLoading(false); }
  };

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, [k]: e.target.value }));

  return (
    <div className="min-h-screen flex">
      {/* ── Left brand panel ── */}
      <div className="hidden lg:flex lg:w-[52%] auth-gradient relative overflow-hidden flex-col justify-between p-12">
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-24 -right-24 w-80 h-80 bg-indigo-400/20 rounded-full blur-3xl" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 bg-white/15 backdrop-blur-sm rounded-2xl flex items-center justify-center border border-white/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="text-white font-semibold text-lg">Nexus AI</span>
        </div>

        <div className="relative z-10 space-y-5">
          <div>
            <p className="text-white/60 text-sm uppercase tracking-widest font-medium mb-3">Get started free</p>
            <h1 className="text-4xl font-bold text-white leading-snug">Build your own<br />AI workforce</h1>
            <p className="text-white/65 text-lg mt-3 leading-relaxed max-w-sm">
              Set up in minutes. No credit card required. Cancel anytime.
            </p>
          </div>
          <div className="space-y-3">
            {["Free forever plan", "Unlimited AI conversations", "Upload & chat with documents", "Visual workflow builder"].map(t => (
              <div key={t} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                </div>
                <span className="text-white/80 text-sm">{t}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-white/30 text-xs">© 2025 Nexus AI · All rights reserved</p>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-center justify-center p-8 bg-white dark:bg-zinc-950 overflow-y-auto">
        <div className="w-full max-w-sm animate-fade-in py-6">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 bg-primary-600 rounded-xl flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-zinc-900 dark:text-white">Nexus AI</span>
          </div>

          <div className="mb-7">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-white">Create account</h2>
            <p className="text-zinc-500 dark:text-zinc-400 mt-1.5">Start automating in seconds</p>
          </div>

          {error && (
            <div className="mb-4 px-4 py-3 rounded-xl bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 text-rose-600 dark:text-rose-400 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {[
              { k: "username", label: "Username", type: "text", icon: User, placeholder: "johndoe", min: 3 },
              { k: "email", label: "Email", type: "email", icon: Mail, placeholder: "you@example.com" },
            ].map(({ k, label, type, icon: Icon, placeholder, min }) => (
              <div key={k} className="space-y-1.5">
                <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">{label}</label>
                <div className="relative glow-focus rounded-xl">
                  <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input type={type} value={(form as any)[k]} onChange={set(k)} required minLength={min}
                    placeholder={placeholder}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:border-primary-500 transition-colors text-sm" />
                </div>
              </div>
            ))}

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Password</label>
              <div className="relative glow-focus rounded-xl">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input type={showPw ? "text" : "password"} value={form.password} onChange={set("password")} required
                  placeholder="Create a strong password"
                  className="w-full pl-10 pr-10 py-3 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:border-primary-500 transition-colors text-sm" />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {form.password && (
                <div className="flex gap-3 mt-1.5 flex-wrap">
                  {reqs.map(r => (
                    <span key={r.text} className={`text-xs flex items-center gap-1 ${r.ok ? "text-emerald-600 dark:text-emerald-400" : "text-zinc-400"}`}>
                      <CheckCircle2 className="w-3 h-3" />{r.text}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Confirm password</label>
              <div className="relative glow-focus rounded-xl">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input type={showPw ? "text" : "password"} value={form.confirm} onChange={set("confirm")} required
                  placeholder="Repeat password"
                  className={`w-full pl-10 pr-4 py-3 rounded-xl border bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none transition-colors text-sm ${form.confirm && form.confirm !== form.password ? "border-rose-400 focus:border-rose-400" : "border-zinc-200 dark:border-zinc-800 focus:border-primary-500"}`} />
              </div>
            </div>

            <button type="submit" disabled={loading}
              className="w-full py-3 rounded-xl bg-primary-600 hover:bg-primary-700 disabled:opacity-60 text-white font-medium text-sm transition-all flex items-center justify-center gap-2 shadow-glow mt-1">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Creating account…</> : "Create account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-zinc-500 dark:text-zinc-400">
            Already have an account?{" "}
            <Link href="/login" className="text-primary-600 dark:text-primary-400 font-medium hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}