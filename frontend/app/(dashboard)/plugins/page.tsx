"use client";

import { useState, useEffect } from "react";
import { Puzzle, Plus, Loader2, Trash2, Check, AlertCircle, Globe } from "lucide-react";
import { listCustomTools, createCustomTool, deleteCustomTool } from "@/lib/api";

export default function PluginsPage() {
  const [tools, setTools] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<{ ok: boolean; msg: string } | null>(null);
  const [form, setForm] = useState({ name: "", description: "", endpoint_url: "", method: "POST", schema: '{\n  "type": "object",\n  "properties": {\n    "query": { "type": "string" }\n  }\n}' });

  const flash = (ok: boolean, msg: string) => { setToast({ ok, msg }); setTimeout(() => setToast(null), 3500); };
  const load = async () => { setLoading(true); try { const d = await listCustomTools(); setTools(d.tools || []); } catch {} setLoading(false); };
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!form.name.trim() || !form.endpoint_url.trim() || busy) return;
    let schema: any = {};
    try { schema = JSON.parse(form.schema || "{}"); } catch { return flash(false, "Parameters must be valid JSON"); }
    setBusy(true);
    try {
      await createCustomTool({ name: form.name.trim(), description: form.description, endpoint_url: form.endpoint_url.trim(), method: form.method, params_schema: schema });
      setForm({ ...form, name: "", description: "", endpoint_url: "" });
      await load(); flash(true, "Plugin registered — agents can use it now");
    } catch (e: any) { flash(false, e.message); }
    setBusy(false);
  };
  const remove = async (id: string, name: string) => {
    if (!confirm(`Delete plugin "${name}"?`)) return;
    await deleteCustomTool(id); await load(); flash(true, "Plugin removed");
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 animate-fade-in">
      {toast && (
        <div className={`fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-card-lg text-sm font-medium ${toast.ok ? "bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300" : "bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300"}`}>
          {toast.ok ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}{toast.msg}
        </div>
      )}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white flex items-center gap-2.5"><Puzzle className="w-6 h-6 text-primary-500" />Plugins</h1>
        <p className="text-zinc-500 dark:text-zinc-400 text-sm mt-1">
          Extend the agents with your own tools. Register any HTTP endpoint as a plugin — the agents can call it like a built-in tool.
        </p>
      </div>

      <div className="grid md:grid-cols-[1.1fr_1fr] gap-5">
        {/* Register form */}
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-card p-5 space-y-3">
          <h3 className="font-semibold text-zinc-900 dark:text-white">Register a plugin</h3>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Tool name (e.g. weather_lookup)"
            className="w-full px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-sm focus:outline-none focus:border-primary-400" />
          <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="What does it do?"
            className="w-full px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-sm focus:outline-none focus:border-primary-400" />
          <div className="flex gap-2">
            <select value={form.method} onChange={(e) => setForm({ ...form, method: e.target.value })}
              className="px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-sm focus:outline-none">
              <option>POST</option><option>GET</option>
            </select>
            <input value={form.endpoint_url} onChange={(e) => setForm({ ...form, endpoint_url: e.target.value })} placeholder="https://api.example.com/tool"
              className="flex-1 px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-sm font-mono focus:outline-none focus:border-primary-400" />
          </div>
          <div>
            <label className="text-xs text-zinc-400">Parameters (JSON Schema)</label>
            <textarea value={form.schema} onChange={(e) => setForm({ ...form, schema: e.target.value })} rows={6}
              className="w-full mt-1 px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-xs font-mono focus:outline-none focus:border-primary-400" />
          </div>
          <button onClick={create} disabled={busy || !form.name.trim() || !form.endpoint_url.trim()}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-semibold">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}Register plugin
          </button>
        </div>

        {/* Installed */}
        <div className="space-y-3">
          <h3 className="font-semibold text-zinc-900 dark:text-white text-sm">Installed plugins</h3>
          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-primary-500" /></div>
          ) : tools.length === 0 ? (
            <div className="text-sm text-zinc-400 border border-dashed border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 text-center">
              No plugins yet. Register one to give your agents a new capability.
            </div>
          ) : tools.map((t) => (
            <div key={t.id} className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-card p-4">
              <div className="flex items-start justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Puzzle className="w-4 h-4 text-primary-500" />
                    <span className="font-semibold text-zinc-800 dark:text-zinc-100 font-mono text-sm">{t.name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-500">{t.method}</span>
                  </div>
                  {t.description && <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">{t.description}</p>}
                  <p className="text-[11px] text-zinc-400 mt-1 flex items-center gap-1 truncate"><Globe className="w-3 h-3" />{t.endpoint_url}</p>
                </div>
                <button onClick={() => remove(t.id, t.name)} className="p-1.5 text-zinc-400 hover:text-rose-500 rounded-lg"><Trash2 className="w-3.5 h-3.5" /></button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
