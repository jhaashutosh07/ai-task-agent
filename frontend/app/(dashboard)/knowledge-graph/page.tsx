"use client";

import { useState, useCallback } from "react";
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { Share2, Loader2, Sparkles, AlertCircle } from "lucide-react";
import { getKnowledgeGraph } from "@/lib/api";

const TYPE_COLOR: Record<string, string> = {
  person: "#8b5cf6", org: "#3b82f6", concept: "#6366f1",
  tech: "#06b6d4", place: "#f59e0b",
};

export default function KnowledgeGraphPage() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");

  const build = useCallback(async () => {
    setLoading(true); setError(""); setNote("");
    try {
      const g = await getKnowledgeGraph();
      if (g.note) setNote(g.note);
      const raw = g.nodes || [];
      const cx = 400, cy = 260, R = 220;
      const rfNodes = raw.map((n: any, i: number) => {
        const a = (2 * Math.PI * i) / Math.max(raw.length, 1);
        return {
          id: String(n.id),
          position: { x: cx + R * Math.cos(a) + (i % 2 ? 40 : -40), y: cy + R * Math.sin(a) },
          data: { label: n.label },
          style: {
            background: TYPE_COLOR[n.type] || "#64748b", color: "white", border: "none",
            borderRadius: 12, padding: "8px 12px", fontSize: 12, fontWeight: 600,
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          },
        };
      });
      const rfEdges = (g.edges || []).map((e: any, i: number) => ({
        id: `e${i}`, source: String(e.source), target: String(e.target),
        label: e.label, animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: "#a5b4fc" }, labelStyle: { fontSize: 10, fill: "#6b7280" },
      })).filter((e: any) => rfNodes.some((n: any) => n.id === e.source) && rfNodes.some((n: any) => n.id === e.target));
      setNodes(rfNodes); setEdges(rfEdges);
    } catch (e: any) {
      setError(e.message || "Failed to build graph");
    }
    setLoading(false);
  }, []);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-5 animate-fade-in">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white flex items-center gap-2.5">
            <Share2 className="w-6 h-6 text-primary-500" />Knowledge Graph
          </h1>
          <p className="text-zinc-500 dark:text-zinc-400 text-sm mt-1">
            Entities and relationships automatically extracted from your uploaded documents.
          </p>
        </div>
        <button onClick={build} disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-semibold transition-colors">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {loading ? "Extracting…" : "Build graph"}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-rose-500 bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 rounded-xl px-4 py-3">
          <AlertCircle className="w-4 h-4" />{error}
        </div>
      )}
      {note && <p className="text-sm text-zinc-400">{note}</p>}

      <div className="h-[560px] rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-card overflow-hidden">
        {nodes.length === 0 && !loading ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-zinc-400 gap-2">
            <Share2 className="w-10 h-10 opacity-40" />
            <p className="text-sm">Upload documents, then click <b>Build graph</b> to visualise the concepts.</p>
          </div>
        ) : (
          <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
            <Background gap={16} color="#e5e7eb" />
            <Controls showInteractive={false} />
          </ReactFlow>
        )}
      </div>

      {nodes.length > 0 && (
        <div className="flex flex-wrap gap-3 text-xs">
          {Object.entries(TYPE_COLOR).map(([t, c]) => (
            <span key={t} className="inline-flex items-center gap-1.5 text-zinc-500 capitalize">
              <span className="w-2.5 h-2.5 rounded" style={{ background: c }} />{t}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
