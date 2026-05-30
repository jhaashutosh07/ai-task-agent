"use client";

import { useState, useRef, useEffect } from "react";
import { Upload, FileText, Trash2, Search, Loader2, CheckCircle2, AlertCircle, X, Database } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const PREFIX = "/api/v1";
const auth = () => ({ Authorization: `Bearer ${typeof window !== "undefined" ? localStorage.getItem("access_token") || "" : ""}` });

async function listDocs() { const r = await fetch(`${API}${PREFIX}/rag/documents`, { headers: auth() }); return r.json(); }
async function deleteDocs(id: string) { await fetch(`${API}${PREFIX}/rag/documents/${id}`, { method: "DELETE", headers: auth() }); }
async function queryRag(query: string) {
  const r = await fetch(`${API}${PREFIX}/rag/query`, { method: "POST", headers: { ...auth(), "Content-Type": "application/json" }, body: JSON.stringify({ query, n_results: 5 }) });
  return r.json();
}

interface Doc { id: string; filename: string; file_type: string; chunk_count: number; char_count: number; ingested_at: string; }
interface Chunk { id: string; content: string; score: number; filename: string; chunk_index: number; }

const TYPE_COLOR: Record<string, string> = {
  pdf: "bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400",
  txt: "bg-sky-50 dark:bg-sky-500/10 text-sky-600 dark:text-sky-400",
  md:  "bg-violet-50 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400",
  html:"bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400",
};

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [results, setResults] = useState<Chunk[]>([]);
  const [query, setQuery] = useState("");
  const [uploading, setUploading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [toast, setToast] = useState<{ type: "ok" | "err"; msg: string } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const showToast = (type: "ok" | "err", msg: string) => { setToast({ type, msg }); setTimeout(() => setToast(null), 3500); };
  const reload = async () => { try { const d = await listDocs(); setDocs(d.documents || []); } catch {} };

  useEffect(() => { reload(); }, []);

  const upload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    let ok = 0, fail = 0;
    for (const file of Array.from(files)) {
      const fd = new FormData(); fd.append("file", file);
      try {
        const r = await fetch(`${API}${PREFIX}/rag/ingest`, { method: "POST", headers: auth(), body: fd });
        if (r.ok) ok++; else { const e = await r.json(); throw new Error(e.detail); }
      } catch (e: any) { fail++; showToast("err", `Failed: ${file.name} — ${e.message}`); }
    }
    if (ok > 0) showToast("ok", `${ok} document${ok > 1 ? "s" : ""} ingested successfully`);
    await reload();
    setUploading(false);
  };

  const remove = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"?`)) return;
    await deleteDocs(id); await reload();
    showToast("ok", `"${name}" removed`);
  };

  const search = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    try { const d = await queryRag(query); setResults(d.results || []); } catch {}
    setSearching(false);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-5 right-5 z-50 flex items-center gap-3 px-4 py-3 rounded-2xl shadow-card-lg text-sm font-medium animate-slide-up ${toast.type === "ok" ? "bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/25" : "bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-500/25"}`}>
          {toast.type === "ok" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {toast.msg}
          <button onClick={() => setToast(null)}><X className="w-3.5 h-3.5 opacity-60 hover:opacity-100" /></button>
        </div>
      )}

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white flex items-center gap-2.5">
          <Database className="w-6 h-6 text-primary-500" />Documents
        </h1>
        <p className="text-zinc-500 dark:text-zinc-400 text-sm mt-1">
          Upload files to give the AI context from your own documents. Supports PDF, TXT, MD, HTML.
        </p>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); upload(e.dataTransfer.files); }}
        onClick={() => fileRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${dragOver ? "border-primary-500 bg-primary-50 dark:bg-primary-500/10" : "border-zinc-200 dark:border-zinc-700 hover:border-primary-400 hover:bg-zinc-50 dark:hover:bg-zinc-900"}`}>
        <input ref={fileRef} type="file" multiple accept=".pdf,.txt,.md,.html" className="hidden" onChange={e => upload(e.target.files)} />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
            <p className="text-sm font-medium text-primary-600 dark:text-primary-400">Processing documents…</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 bg-primary-50 dark:bg-primary-500/10 rounded-2xl flex items-center justify-center">
              <Upload className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="font-semibold text-zinc-800 dark:text-zinc-100 text-sm">Drop files here or click to upload</p>
              <p className="text-zinc-400 text-xs mt-1">PDF, TXT, Markdown, HTML — any size</p>
            </div>
          </div>
        )}
      </div>

      {/* Documents list */}
      {docs.length > 0 && (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-card overflow-hidden">
          <div className="px-5 py-3.5 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
            <h3 className="font-semibold text-zinc-900 dark:text-white text-sm">{docs.length} document{docs.length !== 1 ? "s" : ""} ingested</h3>
          </div>
          <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {docs.map(doc => (
              <div key={doc.id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                <div className="w-9 h-9 bg-zinc-100 dark:bg-zinc-800 rounded-xl flex items-center justify-center flex-shrink-0">
                  <FileText className="w-4 h-4 text-zinc-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-zinc-800 dark:text-zinc-100 truncate">{doc.filename}</p>
                  <p className="text-xs text-zinc-400 mt-0.5">{doc.chunk_count} chunks · {(doc.char_count / 1000).toFixed(1)}k chars · {new Date(doc.ingested_at).toLocaleDateString()}</p>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-lg uppercase ${TYPE_COLOR[doc.file_type] || "bg-zinc-100 dark:bg-zinc-800 text-zinc-500"}`}>{doc.file_type}</span>
                <button onClick={() => remove(doc.id, doc.filename)} className="p-1.5 text-zinc-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 rounded-lg transition-colors">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* RAG Query */}
      <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-card p-5">
        <h3 className="font-semibold text-zinc-900 dark:text-white text-sm mb-3 flex items-center gap-2">
          <Search className="w-4 h-4 text-primary-500" />Test your documents
        </h3>
        <form onSubmit={search} className="flex gap-2">
          <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Ask something about your documents…"
            className="flex-1 px-4 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-sm text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:border-primary-400 transition-colors" />
          <button type="submit" disabled={!query.trim() || searching}
            className="px-4 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-xl text-sm font-medium transition-colors flex items-center gap-2">
            {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}Search
          </button>
        </form>
        {results.length > 0 && (
          <div className="mt-4 space-y-3">
            {results.map((r, i) => (
              <div key={r.id} className="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl border border-zinc-200 dark:border-zinc-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">[{r.filename}] chunk {r.chunk_index}</span>
                  <span className={`text-xs font-semibold ${r.score > 0.7 ? "text-emerald-600 dark:text-emerald-400" : r.score > 0.4 ? "text-amber-600 dark:text-amber-400" : "text-zinc-500"}`}>{(r.score * 100).toFixed(0)}% match</span>
                </div>
                <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed line-clamp-4">{r.content}</p>
              </div>
            ))}
          </div>
        )}
        {docs.length === 0 && <p className="text-xs text-zinc-400 mt-2">Upload a document first to test RAG queries.</p>}
      </div>
    </div>
  );
}