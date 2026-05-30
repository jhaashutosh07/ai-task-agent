"use client";

import { useState, useRef, useEffect } from "react";
import { sendMessage } from "@/lib/api";

interface Msg { id: string; role: "user" | "assistant"; content: string; }

export default function ChatInterface() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const add = (role: "user" | "assistant", content: string) =>
    setMessages(prev => [...prev, { id: crypto.randomUUID(), role, content }]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput("");
    setError("");
    add("user", msg);
    setLoading(true);
    try {
      const res = await sendMessage(msg);
      add("assistant", res.response ?? "(empty response)");
    } catch (err: any) {
      setError(err.message || "Request failed");
      add("assistant", "Error: " + (err.message || "Request failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100%", fontFamily:"Inter,sans-serif" }}>
      {/* messages */}
      <div style={{ flex:1, overflowY:"auto", padding:"1.5rem", display:"flex", flexDirection:"column", gap:"1rem" }}>
        {messages.length === 0 && (
          <p style={{ textAlign:"center", color:"#94a3b8", marginTop:"4rem" }}>
            Send a message to start chatting
          </p>
        )}
        {messages.map(m => (
          <div key={m.id} style={{ display:"flex", justifyContent: m.role==="user" ? "flex-end" : "flex-start" }}>
            <div style={{
              maxWidth:"75%", padding:"0.75rem 1rem", borderRadius:"1rem",
              background: m.role==="user" ? "#4f46e5" : "#ffffff",
              color: m.role==="user" ? "#ffffff" : "#0f172a",
              border: m.role==="user" ? "none" : "1px solid #e2e8f0",
              boxShadow:"0 1px 3px rgba(0,0,0,0.07)",
              fontSize:"0.875rem", lineHeight:"1.6", whiteSpace:"pre-wrap",
            }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display:"flex", alignItems:"center", gap:"0.5rem", color:"#94a3b8", fontSize:"0.875rem" }}>
            <span>●</span><span>Thinking…</span>
          </div>
        )}
        {error && <p style={{ color:"#ef4444", fontSize:"0.75rem" }}>{error}</p>}
        <div ref={bottomRef} />
      </div>

      {/* input */}
      <form onSubmit={submit} style={{ padding:"1rem", borderTop:"1px solid #e2e8f0", background:"#fff", display:"flex", gap:"0.5rem" }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key==="Enter" && !e.shiftKey) { e.preventDefault(); submit(e as any); }}}
          placeholder="Message Nexus AI…"
          rows={1}
          style={{ flex:1, padding:"0.75rem 1rem", borderRadius:"0.75rem", border:"1px solid #e2e8f0",
            outline:"none", resize:"none", fontFamily:"inherit", fontSize:"0.875rem" }}
        />
        <button type="submit" disabled={!input.trim() || loading}
          style={{ padding:"0.75rem 1.25rem", background: (!input.trim()||loading) ? "#c7d2fe" : "#4f46e5",
            color:"#fff", border:"none", borderRadius:"0.75rem", cursor: loading?"not-allowed":"pointer",
            fontSize:"0.875rem", fontWeight:600 }}>
          {loading ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}