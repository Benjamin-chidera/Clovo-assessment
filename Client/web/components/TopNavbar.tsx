'use client';

import React from 'react';
import Link from 'next/link';
import { Bell, ShieldAlert, Sparkles, CheckCircle2 } from 'lucide-react';
import { useSafetyTriageStore } from '../stores/useSafetyTriageStore';

interface TopNavbarProps {
  title: string;
  subtitle?: string;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({ title, subtitle }) => {
  const { events, isConnected } = useSafetyTriageStore();
  const openAlerts = events.filter((e) => e.status !== 'resolved');
  const criticalAlerts = openAlerts.filter(
    (e) => e.risk_level === 'critical' || e.risk_level === 'high'
  );

  return (
    <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-500 font-medium mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Real-time Socket Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
            }`}
          />
          <span>{isConnected ? 'Real-Time Stream' : 'Reconnecting...'}</span>
        </div>

        {/* Safety Alert Status */}
        {criticalAlerts.length > 0 ? (
          <Link
            href="/safety-events"
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-red-50 text-red-700 border border-red-200 text-xs font-bold shadow-xs hover:bg-red-100 transition-colors"
          >
            <ShieldAlert className="w-4 h-4 text-red-600 animate-bounce" />
            <span>{criticalAlerts.length} High/Critical Alerts</span>
          </Link>
        ) : (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>All Clear</span>
          </div>
        )}

        {/* AI Health Badge */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Amy AI · gemma4</span>
        </div>
      </div>
    </header>
  );
};
