"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ShieldAlert,
  MessageSquare,
  Users,
  ExternalLink,
  Activity,
  UserCheck,
} from "lucide-react";
import { useSafetyTriageStore } from "../stores/useSafetyTriageStore";
import { useAuthStore } from "../stores/useAuthStore";

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { events, isConnected } = useSafetyTriageStore();
  const { clinician } = useAuthStore();

  const openAlertsCount = events.filter((e) => e.status !== "resolved").length;
  const criticalCount = events.filter(
    (e) =>
      e.status !== "resolved" &&
      (e.risk_level === "critical" || e.risk_level === "high"),
  ).length;

  const navItems = [
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
      badge: null,
    },
    {
      name: "Safety Triage",
      href: "/safety-events",
      icon: ShieldAlert,
      badge: openAlertsCount > 0 ? openAlertsCount : null,
      badgeColor:
        criticalCount > 0
          ? "bg-red-500 text-white animate-pulse"
          : "bg-amber-500 text-white",
    },
    {
      name: "Conversations",
      href: "/conversations",
      icon: MessageSquare,
      badge: null,
    },
    {
      name: "Patients",
      href: "/patients",
      icon: Users,
      badge: null,
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div>
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm shadow-indigo-200">
              C
            </div>
            <div>
              <h1 className="font-bold text-slate-900 text-base leading-tight tracking-tight">
                Clovo Admin
              </h1>
              <p className="text-xs text-slate-500 font-medium">
                Clinician Oversight
              </p>
            </div>
          </div>
          <div
            className={`w-2.5 h-2.5 rounded-full ${
              isConnected
                ? "bg-emerald-500 shadow-sm shadow-emerald-300"
                : "bg-amber-400 animate-ping"
            }`}
            title={
              isConnected
                ? "Live Socket.IO Connected"
                : "Connecting to Socket.IO..."
            }
          />
        </div>

        {/* Navigation Menu */}
        <nav className="p-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700 shadow-xs"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`w-4 h-4 ${isActive ? "text-indigo-600" : "text-slate-400"}`}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge !== null && (
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                      item.badgeColor || "bg-indigo-600 text-white"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Tools & Profile */}
      <div className="p-4 border-t border-slate-100 space-y-3">
        {/* Langfuse Observability Link */}
        <a
          href="http://localhost:3000"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200/80 text-xs font-semibold text-slate-700 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-indigo-600" />
            <span>Langfuse LLM Traces</span>
          </div>
          <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
        </a>

        {/* Clinician Profile */}
        <div className="flex items-center gap-3 p-2 bg-slate-50/60 rounded-xl border border-slate-100">
          <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 font-semibold text-xs">
            <UserCheck className="w-4 h-4 text-slate-600" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-slate-800 truncate">
              {clinician.name}
            </p>
            <p className="text-[11px] text-slate-500 truncate">
              {clinician.role}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
};
