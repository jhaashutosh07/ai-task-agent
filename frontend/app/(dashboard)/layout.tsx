"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sparkles, MessageSquare, LayoutDashboard, GitBranch,
  Wrench, Settings, Menu, X, LogOut, ChevronRight, FileText, Swords,
} from "lucide-react";
import AuthGuard from "@/components/AuthGuard";
import { useStore } from "@/lib/store";
import { logout } from "@/lib/auth";
import ThemeToggle from "@/components/ThemeToggle";

const navItems = [
  { href: "/chat",      label: "Chat",       icon: MessageSquare,  badge: null },
  { href: "/dashboard", label: "Dashboard",  icon: LayoutDashboard, badge: null },
  { href: "/documents", label: "Documents",  icon: FileText,        badge: "RAG" },
  { href: "/playground", label: "Playground", icon: Swords,         badge: "NEW" },
  { href: "/workflows", label: "Workflows",  icon: GitBranch,       badge: null },
  { href: "/tools",     label: "Tools",      icon: Wrench,          badge: null },
  { href: "/settings",  label: "Settings",   icon: Settings,        badge: null },
];

function Avatar({ name }: { name: string }) {
  const initials = name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
  const colors = ["bg-violet-500", "bg-indigo-500", "bg-blue-500", "bg-emerald-500", "bg-rose-500"];
  const color = colors[name.charCodeAt(0) % colors.length];
  return (
    <div className={`w-8 h-8 ${color} rounded-full flex items-center justify-center text-white text-xs font-semibold flex-shrink-0`}>
      {initials || "?"}
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { user, setUser } = useStore();

  const handleLogout = () => { logout(); setUser(null); window.location.href = "/login"; };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 flex">
        {open && <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={() => setOpen(false)} />}

        {/* Sidebar */}
        <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-60 bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 flex flex-col transition-transform duration-200 ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
          {/* Logo */}
          <div className="px-4 py-5 flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800">
            <Link href="/chat" className="flex items-center gap-2.5" onClick={() => setOpen(false)}>
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-violet-600 rounded-xl flex items-center justify-center shadow-glow">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <span className="font-bold text-zinc-900 dark:text-white text-sm">Nexus AI</span>
                <span className="block text-[10px] text-zinc-400 leading-none">v2.0</span>
              </div>
            </Link>
            <div className="flex items-center gap-1">
              <ThemeToggle />
              <button onClick={() => setOpen(false)} className="lg:hidden p-1 text-zinc-400"><X className="w-4 h-4" /></button>
            </div>
          </div>

          {/* Nav */}
          <nav className="flex-1 p-3 space-y-0.5">
            {navItems.map(({ href, label, icon: Icon, badge }) => {
              const active = pathname === href || pathname.startsWith(href + "/");
              return (
                <Link key={href} href={href} onClick={() => setOpen(false)}
                  className={`group flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    active
                      ? "bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-400"
                      : "text-zinc-500 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-white"
                  }`}>
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${active ? "text-primary-600 dark:text-primary-400" : ""}`} />
                    {label}
                  </div>
                  <div className="flex items-center gap-1.5">
                    {badge && <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-violet-100 dark:bg-violet-500/15 text-violet-600 dark:text-violet-400">{badge}</span>}
                    {active && <ChevronRight className="w-3.5 h-3.5 text-primary-500" />}
                  </div>
                </Link>
              );
            })}
          </nav>

          {/* User footer */}
          <div className="p-3 border-t border-zinc-100 dark:border-zinc-800">
            <div className="flex items-center gap-2.5 p-2 rounded-xl hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors group cursor-default">
              <Avatar name={user?.username || "U"} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-zinc-800 dark:text-zinc-100 truncate">{user?.username || "User"}</p>
                <p className="text-xs text-zinc-400 truncate">{user?.email || ""}</p>
              </div>
            </div>
            <button onClick={handleLogout}
              className="w-full mt-1 flex items-center gap-2 px-3 py-2 text-sm text-zinc-500 dark:text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 rounded-xl transition-colors">
              <LogOut className="w-4 h-4" />
              Sign out
            </button>
          </div>
        </aside>

        {/* Main */}
        <div className="flex-1 flex flex-col min-w-0">
          <header className="lg:hidden bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-4 py-3 flex items-center gap-3">
            <button onClick={() => setOpen(true)} className="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-500">
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-gradient-to-br from-primary-500 to-violet-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="font-semibold text-zinc-900 dark:text-white text-sm">Nexus AI</span>
            </div>
          </header>
          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </div>
    </AuthGuard>
  );
}