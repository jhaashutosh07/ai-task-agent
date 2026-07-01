"use client";

import { useState, useEffect } from "react";
import {
  Activity, Cpu, DollarSign, MessageSquare, Zap, Clock,
  CheckCircle, Loader2, RefreshCw, Database, Brain, Sparkles, FileText,
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import {
  getInfo, getUsageAnalytics, getProviderStatus, getObservabilityMetrics,
} from "@/lib/api";
import { useStore } from "@/lib/store";

const FREE_PROVIDERS = new Set(["groq", "openrouter", "cerebras", "gemini", "ollama"]);
const PROVIDER_COLORS: Record<string, string> = {
  openai: "#10b981", anthropic: "#8b5cf6", gemini: "#3b82f6",
  groq: "#f97316", openrouter: "#ec4899", cerebras: "#06b6d4", ollama: "#f59e0b",
};
const INTENT_COLORS: Record<string, string> = { chat: "#6366f1", task: "#8b5cf6", cache: "#f59e0b" };

function StatCard({ title, value, icon, color, sub }: any) {
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-100 dark:border-zinc-800 shadow-card">
      <div className={`inline-flex p-2 rounded-xl mb-3 ${color}`}>{icon}</div>
      <div className="text-2xl font-bold text-zinc-900 dark:text-white">{value}</div>
      <div className="text-sm font-medium text-zinc-600 dark:text-zinc-300 mt-0.5">{title}</div>
      {sub && <div className="text-xs text-zinc-400 mt-0.5">{sub}</div>}
    </div>
  );
}

function Panel({ title, icon, children }: any) {
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-100 dark:border-zinc-800 shadow-card">
      <h3 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2 mb-4">{icon}{title}</h3>
      {children}
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useStore();
  const [loading, setLoading] = useState(true);
  const [info, setInfo] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const [providers, setProviders] = useState<any>(null);

  const load = async () => {
    setLoading(true);
    const [i, m, u, p] = await Promise.allSettled([
      getInfo(), getObservabilityMetrics(), getUsageAnalytics(), getProviderStatus(),
    ]);
    if (i.status === "fulfilled") setInfo(i.value);
    if (m.status === "fulfilled") setMetrics(m.value);
    if (u.status === "fulfilled") setUsage(u.value);
    if (p.status === "fulfilled") setProviders(p.value);
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-full min-h-64">
      <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
    </div>
  );

  const totalRequests = metrics?.total_requests ?? 0;
  const cacheHitRate = metrics?.cache_hit_rate != null ? `${(metrics.cache_hit_rate * 100).toFixed(0)}%` : "0%";
  const avgLatency = metrics?.avg_latency_ms != null ? `${(metrics.avg_latency_ms / 1000).toFixed(2)}s` : "—";
  const totalCost = usage?.total_cost != null ? `$${usage.total_cost.toFixed(4)}` : "$0.00";
  const totalTokens = usage?.total_tokens ? (usage.total_tokens.input + usage.total_tokens.output) : 0;
  const ragRequests = metrics?.rag_requests ?? 0;

  const intentData = Object.entries(metrics?.intent_distribution || {}).map(([name, value]) => ({
    name, value: value as number, color: INTENT_COLORS[name] || "#94a3b8",
  }));
  const dailyCostData = Object.entries(usage?.daily_costs || {}).map(([date, cost]) => ({
    date: date.slice(5), cost: Number(cost),
  }));
  const providerList = providers?.providers || [];
  const providerDist = Object.entries(usage?.by_provider || {}).map(([name, v]: any) => ({
    name, value: v.requests || 0, color: PROVIDER_COLORS[name] || "#94a3b8",
  })).filter((d) => d.value > 0);

  const statCards = [
    { title: "Total Requests", value: totalRequests.toLocaleString(), icon: <MessageSquare className="w-4 h-4" />, color: "bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400", sub: "Chat pipeline" },
    { title: "Cache Hit Rate", value: cacheHitRate, icon: <Zap className="w-4 h-4" />, color: "bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400", sub: "Semantic cache" },
    { title: "Avg Latency", value: avgLatency, icon: <Clock className="w-4 h-4" />, color: "bg-cyan-50 dark:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400", sub: `p95 ${metrics?.p95_latency_ms ? (metrics.p95_latency_ms / 1000).toFixed(2) + "s" : "—"}` },
    { title: "Total Cost", value: totalCost, icon: <DollarSign className="w-4 h-4" />, color: "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400", sub: "Last 30 days" },
    { title: "Tokens Used", value: totalTokens >= 1000 ? `${(totalTokens / 1000).toFixed(1)}K` : totalTokens, icon: <Cpu className="w-4 h-4" />, color: "bg-violet-50 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400", sub: "Input + output" },
    { title: "RAG Queries", value: ragRequests.toLocaleString(), icon: <FileText className="w-4 h-4" />, color: "bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400", sub: "Document-grounded" },
  ];

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Dashboard</h1>
          <p className="text-zinc-500 dark:text-zinc-400 mt-1 text-sm">Live performance and usage for your workspace.</p>
        </div>
        <button onClick={load} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-white text-sm font-medium shadow-card transition-colors">
          <RefreshCw className="w-3.5 h-3.5" />Refresh
        </button>
      </div>

      {/* System status */}
      <div className="bg-white dark:bg-zinc-900 rounded-2xl p-4 border border-zinc-100 dark:border-zinc-800 shadow-card flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-full bg-emerald-500/15">
            <CheckCircle className="w-5 h-5 text-emerald-500" />
          </div>
          <div>
            <p className="font-medium text-zinc-900 dark:text-white">System Healthy</p>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              {info?.tools?.length ?? 0} tools · {info?.agents?.length ?? 0} agents · v{info?.version ?? "2.0"}
            </p>
          </div>
        </div>
        <div className="text-sm text-zinc-500 dark:text-zinc-400">
          Active provider: <span className="text-zinc-900 dark:text-white font-medium capitalize">{providers?.default ?? "openai"}</span>
        </div>
      </div>

      {/* Stat grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {statCards.map((c) => <StatCard key={c.title} {...c} />)}
      </div>

      {/* LLM providers */}
      <Panel title="LLM Providers" icon={<Brain className="w-4 h-4 text-violet-500 mr-1" />}>
        {providerList.length === 0 ? (
          <p className="text-sm text-zinc-400">No providers reported.</p>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {providerList.map((p: any) => (
              <div key={p.name} className="flex items-center gap-3 p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-100 dark:border-zinc-800">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: PROVIDER_COLORS[p.name] || "#94a3b8" }} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-zinc-800 dark:text-zinc-100 capitalize">{p.name}</p>
                  <p className="text-xs text-zinc-400">
                    {FREE_PROVIDERS.has(p.name)
                      ? "Free"
                      : `$${p.cost_per_1k?.input ?? 0}/$${p.cost_per_1k?.output ?? 0} per 1K`}
                  </p>
                </div>
                {FREE_PROVIDERS.has(p.name) && (
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">FREE</span>
                )}
                <span className={`w-1.5 h-1.5 rounded-full ${p.healthy ? "bg-emerald-500" : "bg-zinc-300 dark:bg-zinc-600"}`} title={p.healthy ? "healthy" : "not checked"} />
              </div>
            ))}
          </div>
        )}
        {providers?.fallback_chain && (
          <p className="text-xs text-zinc-400 mt-3">
            Fallback order: {providers.fallback_chain.join(" → ")}
          </p>
        )}
      </Panel>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-5">
        <Panel title="Request Types" icon={<Sparkles className="w-4 h-4 text-primary-500 mr-1" />}>
          <div className="h-56">
            {intentData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-zinc-400">No requests yet — start chatting.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={intentData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={4} dataKey="value">
                    {intentData.map((e, i) => <Cell key={i} fill={e.color} />)}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e5e7eb" }} />
                  <Legend verticalAlign="middle" align="right" layout="vertical" wrapperStyle={{ fontSize: 12, textTransform: "capitalize" }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </Panel>

        <Panel title="Cost Trend (30d)" icon={<DollarSign className="w-4 h-4 text-emerald-500 mr-1" />}>
          <div className="h-56">
            {dailyCostData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-zinc-400">No spend recorded yet.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dailyCostData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.4} />
                  <XAxis dataKey="date" fontSize={11} stroke="#9ca3af" />
                  <YAxis fontSize={11} stroke="#9ca3af" tickFormatter={(v) => `$${v}`} />
                  <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e5e7eb" }} formatter={(v: number) => [`$${v.toFixed(4)}`, "Cost"]} />
                  <Bar dataKey="cost" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Panel>
      </div>

      {/* Provider usage distribution (if any) */}
      {providerDist.length > 0 && (
        <Panel title="Requests by Provider" icon={<Activity className="w-4 h-4 text-blue-500 mr-1" />}>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={providerDist} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.4} />
                <XAxis type="number" fontSize={11} stroke="#9ca3af" />
                <YAxis type="category" dataKey="name" fontSize={11} stroke="#9ca3af" width={80} />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e5e7eb" }} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {providerDist.map((e, i) => <Cell key={i} fill={e.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      )}
    </div>
  );
}
