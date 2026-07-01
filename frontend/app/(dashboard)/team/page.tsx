"use client";

import { useState, useEffect } from "react";
import { Users, Plus, Loader2, UserPlus, Crown, Check, AlertCircle } from "lucide-react";
import { listWorkspaces, createWorkspace, inviteMember, listMembers } from "@/lib/api";

export default function TeamPage() {
  const [workspaces, setWorkspaces] = useState<any[]>([]);
  const [active, setActive] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");
  const [invite, setInvite] = useState("");
  const [toast, setToast] = useState<{ ok: boolean; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const flash = (ok: boolean, msg: string) => { setToast({ ok, msg }); setTimeout(() => setToast(null), 3500); };

  const load = async () => {
    setLoading(true);
    try {
      const d = await listWorkspaces();
      setWorkspaces(d.workspaces || []);
      if (d.workspaces?.length && !active) selectWs(d.workspaces[0]);
    } catch {}
    setLoading(false);
  };
  const selectWs = async (ws: any) => {
    setActive(ws);
    try { const m = await listMembers(ws.id); setMembers(m.members || []); } catch { setMembers([]); }
  };
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!newName.trim() || busy) return;
    setBusy(true);
    try { const ws = await createWorkspace(newName.trim()); setNewName(""); await load(); flash(true, `Workspace "${ws.name}" created`); }
    catch (e: any) { flash(false, e.message); }
    setBusy(false);
  };
  const doInvite = async () => {
    if (!invite.trim() || !active || busy) return;
    setBusy(true);
    try {
      const r = await inviteMember(active.id, invite.trim());
      setInvite("");
      if (r.added) { flash(true, `Added ${r.username}`); await selectWs(active); }
      else flash(false, `${r.username} is already a member`);
    } catch (e: any) { flash(false, e.message); }
    setBusy(false);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 animate-fade-in">
      {toast && (
        <div className={`fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-card-lg text-sm font-medium ${toast.ok ? "bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300" : "bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300"}`}>
          {toast.ok ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}{toast.msg}
        </div>
      )}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white flex items-center gap-2.5"><Users className="w-6 h-6 text-primary-500" />Workspaces</h1>
        <p className="text-zinc-500 dark:text-zinc-400 text-sm mt-1">Create shared workspaces and invite teammates to collaborate.</p>
      </div>

      {/* Create */}
      <div className="flex gap-2">
        <input value={newName} onChange={(e) => setNewName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && create()}
          placeholder="New workspace name…"
          className="flex-1 px-4 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-sm text-zinc-900 dark:text-white focus:outline-none focus:border-primary-400" />
        <button onClick={create} disabled={busy || !newName.trim()} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-semibold">
          <Plus className="w-4 h-4" />Create
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-primary-500" /></div>
      ) : workspaces.length === 0 ? (
        <div className="text-center py-12 text-zinc-400 text-sm">No workspaces yet — create your first one above.</div>
      ) : (
        <div className="grid md:grid-cols-[1fr_1.4fr] gap-5">
          {/* list */}
          <div className="space-y-2">
            {workspaces.map((ws) => (
              <button key={ws.id} onClick={() => selectWs(ws)}
                className={`w-full text-left p-4 rounded-2xl border transition-colors ${active?.id === ws.id ? "border-primary-300 bg-primary-50 dark:bg-primary-500/10" : "border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:border-zinc-300"}`}>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-zinc-800 dark:text-zinc-100">{ws.name}</span>
                  {ws.role === "owner" && <Crown className="w-3.5 h-3.5 text-amber-500" />}
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">{ws.members} member{ws.members !== 1 ? "s" : ""} · {ws.role}</p>
              </button>
            ))}
          </div>

          {/* members */}
          {active && (
            <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-card p-5">
              <h3 className="font-semibold text-zinc-900 dark:text-white mb-3">{active.name} · members</h3>
              <div className="flex gap-2 mb-4">
                <input value={invite} onChange={(e) => setInvite(e.target.value)} onKeyDown={(e) => e.key === "Enter" && doInvite()}
                  placeholder="Invite by username…"
                  className="flex-1 px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-sm focus:outline-none focus:border-primary-400" />
                <button onClick={doInvite} disabled={busy || !invite.trim()} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-sm font-medium disabled:opacity-50">
                  <UserPlus className="w-4 h-4" />Invite
                </button>
              </div>
              <div className="space-y-1.5">
                {members.map((m) => (
                  <div key={m.user_id} className="flex items-center justify-between px-3 py-2 rounded-xl bg-zinc-50 dark:bg-zinc-800/50">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-lg bg-primary-100 dark:bg-primary-500/15 flex items-center justify-center text-xs font-semibold text-primary-600 dark:text-primary-300">
                        {(m.username || "?").slice(0, 2).toUpperCase()}
                      </div>
                      <span className="text-sm text-zinc-700 dark:text-zinc-200">{m.username || m.user_id.slice(0, 8)}</span>
                    </div>
                    <span className={`text-xs font-medium ${m.role === "owner" ? "text-amber-500" : "text-zinc-400"}`}>{m.role}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
