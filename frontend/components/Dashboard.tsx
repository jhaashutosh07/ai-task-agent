"use client";

import { useState, useEffect } from "react";
import { Activity, Brain, GitBranch, Clock, Database, Cpu, Zap, HardDrive, RefreshCw, ArrowUpRight, FileText } from "lucide-react";
import { getInfo, getMemoryStats, listScheduledTasks, listWorkflows } from "@/lib/api";
import { useStore } from "@/lib/store";

interface Stats { tools: string[]; agents: string[]; workflows: number; tasks: number; memories: number; knowledge: number; }

function StatCard({ title, value, icon, color, sub }: any) {
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-100 dark:border-zinc-800 shadow-card hover:shadow-card-md transition-shadow">
      <div className={`inline-flex p-2 rounded-xl mb-3 ${color}`}>{icon}</div>
      <div className="text-2xl font-bold text-zinc-900 dark:text-white">{value}</div>
      <div className="text-sm font-medium text-zinc-600 dark:text-zinc-300 mt-0.5">{title}</div>
      {sub && <div className="text-xs text-zinc-400 mt-0.5">{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useStore();

  const load = async () => {
    setLoading(true);
    try {
      const [info, memory, tasks, workflows] = await Promise.all([getInfo(), getMemoryStats(), listScheduledTasks(), listWorkflows()]);
      setStats({
        tools: info.tools || [], agents: info.agents || [],
        workflows: workflows.workflows?.length || 0,
        tasks: tasks.tasks?.length || 0,
        memories: memory.vector_memory?.total_memories || 0,
        knowledge: memory.knowledge_base?.total_entries || 0,
      });
    } catch { } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  if (loading) return (
    <div className="flex items-center justify-center h-full min-h-64">
      <RefreshCw className="w-5 h-5 animate-spin text-primary-500" />
    </div>
  );

  const statCards = [
    { title: "Tools", value: stats?.tools.length ?? 0, icon: <Zap className="w-4 h-4" />, color: "bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400", sub: "Active integrations" },
    { title: "AI Agents", value: stats?.agents.length ?? 0, icon: <Brain className="w-4 h-4" />, color: "bg-violet-50 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400", sub: "Specialized models" },
    { title: "Workflows", value: stats?.workflows ?? 0, icon: <GitBranch className="w-4 h-4" />, color: "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400", sub: "Saved automations" },
    { title: "Scheduled", value: stats?.tasks ?? 0, icon: <Clock className="w-4 h-4" />, color: "bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400", sub: "Running tasks" },
    { title: "Memories", value: stats?.memories ?? 0, icon: <Database className="w-4 h-4" />, color: "bg-cyan-50 dark:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400", sub: "Vector embeddings" },
    { title: "Knowledge", value: stats?.knowledge ?? 0, icon: <HardDrive className="w-4 h-4" />, color: "bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400", sub: "Knowledge base entries" },
  ];

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">{greeting}{user?.username ? `, ${user.username}` : ""} 👋</h1>
          <p className="text-zinc-500 dark:text-zinc-400 mt-1 text-sm">Here&apos;s what&apos;s running in your workspace today.</p>
        </div>
        <button onClick={load} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-white text-sm font-medium shadow-card transition-colors">
          <RefreshCw className="w-3.5 h-3.5" />Refresh
        </button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {statCards.map(c => <StatCard key={c.title} {...c} />)}
      </div>

      {/* Two-column section */}
      <div className="grid md:grid-cols-2 gap-5">
        {/* Tools */}
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-100 dark:border-zinc-800 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-blue-500" />Available Tools
            </h3>
            <span className="text-xs text-zinc-400">{stats?.tools.length} active</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {stats?.tools.map(tool => (
              <span key={tool} className="px-2.5 py-1 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-xs text-zinc-600 dark:text-zinc-300 font-medium">
                {tool.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>

        {/* Agents */}
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-100 dark:border-zinc-800 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
              <Brain className="w-4 h-4 text-violet-500" />AI Agents
            </h3>
            <span className="text-xs text-zinc-400">{stats?.agents.length} online</span>
          </div>
          <div className="space-y-2">
            {stats?.agents.map(agent => (
              <div key={agent} className="flex items-center gap-3 p-2.5 rounded-xl bg-zinc-50 dark:bg-zinc-800/50">
                <div className="w-7 h-7 bg-violet-100 dark:bg-violet-500/15 rounded-lg flex items-center justify-center">
                  <Cpu className="w-3.5 h-3.5 text-violet-600 dark:text-violet-400" />
                </div>
                <span className="text-sm font-medium text-zinc-700 dark:text-zinc-200 capitalize">{agent}</span>
                <div className="ml-auto flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-dot" />
                  <span className="text-xs text-emerald-600 dark:text-emerald-400">Ready</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* System status */}
      <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-100 dark:border-zinc-800 shadow-card">
        <h3 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2 mb-4">
          <Activity className="w-4 h-4 text-emerald-500" />System Status
        </h3>
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "API", status: "Operational" },
            { label: "Multi-agent system", status: "Active" },
            { label: "RAG Pipeline", status: "Ready" },
            { label: "Vector memory", status: "Connected" },
          ].map(({ label, status }) => (
            <div key={label} className="flex items-center justify-between p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800/50">
              <span className="text-sm text-zinc-600 dark:text-zinc-300">{label}</span>
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-dot" />{status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}