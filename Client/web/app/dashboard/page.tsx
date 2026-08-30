'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Users,
  ShieldAlert,
  Activity,
  Sparkles,
  ArrowUpRight,
  Clock,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Flame,
} from 'lucide-react';
import { TopNavbar } from '../../components/TopNavbar';
import { SafetyResolutionDrawer } from '../../components/SafetyResolutionDrawer';
import { useSafetyTriageStore, SafetyEventItem } from '../../stores/useSafetyTriageStore';

const SERVER_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DashboardStats {
  total_patients: number;
  open_alerts_count: number;
  critical_alerts_count: number;
  adherence_rate: number;
  ai_safety_score: number;
  recent_alerts: SafetyEventItem[];
}

export default function DashboardPage() {
  const { events, selectedEvent, setSelectedEvent } = useSafetyTriageStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${SERVER_URL}/api/admin/dashboard/stats`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (err) {
        console.error('Failed to load dashboard stats:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  const openEvents = events.filter((e) => e.status !== 'resolved');
  const criticalCount = openEvents.filter((e) => e.risk_level === 'critical' || e.risk_level === 'high').length;

  const severityBadge = (level: string) => {
    switch (level) {
      case 'critical':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-red-100 text-red-800 border border-red-200">Critical</span>;
      case 'high':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-orange-100 text-orange-800 border border-orange-200">High</span>;
      case 'medium':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">Medium</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-200">Low</span>;
    }
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <TopNavbar
        title="Clinical Command Center"
        subtitle="Real-time safety escalations, recovery adherence, and AI coach oversight"
      />

      <div className="p-8 space-y-8 max-w-7xl w-full mx-auto">
        {/* KPI Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Card 1 */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Patients</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats?.total_patients || 1} Enrolled</h3>
              <p className="text-[11px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                100% in active pathways
              </p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600">
              <Users className="w-6 h-6" />
            </div>
          </div>

          {/* Card 2 */}
          <div className={`p-5 rounded-2xl border shadow-xs flex items-center justify-between transition-colors ${
            criticalCount > 0 ? 'bg-red-50/40 border-red-200' : 'bg-white border-slate-200'
          }`}>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Open Safety Alerts</p>
              <h3 className={`text-2xl font-bold mt-1 ${criticalCount > 0 ? 'text-red-700' : 'text-slate-900'}`}>
                {openEvents.length} Alerts
              </h3>
              <p className="text-[11px] font-semibold mt-1 text-slate-500">
                {criticalCount > 0 ? `${criticalCount} urgent (High/Critical)` : 'All stable'}
              </p>
            </div>
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
              criticalCount > 0 ? 'bg-red-100 text-red-600 animate-pulse' : 'bg-amber-50 text-amber-600'
            }`}>
              <ShieldAlert className="w-6 h-6" />
            </div>
          </div>

          {/* Card 3 */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">7-Day Adherence</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats?.adherence_rate || 91.5}%</h3>
              <p className="text-[11px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
                <Flame className="w-3.5 h-3.5 text-orange-500" />
                Active prep consistency
              </p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600">
              <Activity className="w-6 h-6" />
            </div>
          </div>

          {/* Card 4 */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">AI Safety Score</p>
              <h3 className="text-2xl font-bold text-indigo-700 mt-1">{stats?.ai_safety_score || 100}%</h3>
              <p className="text-[11px] text-slate-500 font-medium mt-1 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-500" />
                Langfuse automated evals
              </p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600">
              <Sparkles className="w-6 h-6" />
            </div>
          </div>
        </div>

        {/* Priority Real-Time Safety Feed */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center text-red-600">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Priority Clinical Safety Triage Feed</h3>
                <p className="text-xs text-slate-500">Live incoming escalations from Amy Recovery Coach</p>
              </div>
            </div>
            <Link
              href="/safety-events"
              className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <span>View 4-Tier Board</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-slate-100">
            {openEvents.length === 0 ? (
              <div className="p-12 text-center text-slate-400 space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                <p className="text-sm font-semibold text-slate-700">No Unresolved Safety Alerts</p>
                <p className="text-xs text-slate-400">All patient interactions are within normal recovery boundaries.</p>
              </div>
            ) : (
              openEvents.slice(0, 5).map((event) => (
                <div
                  key={event.id}
                  className="p-5 hover:bg-slate-50/70 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 min-w-0 flex-1">
                    <div className="flex items-center gap-2.5">
                      <span className="font-bold text-sm text-slate-900">
                        {event.patient_name || 'Sarah Jenkins'}
                      </span>
                      <span className="text-xs text-slate-500 font-medium">({event.procedure || 'Knee Surgery'})</span>
                      {severityBadge(event.risk_level)}
                    </div>
                    <p className="text-xs text-slate-700 font-medium leading-relaxed italic bg-amber-50/50 p-2 rounded-lg border border-amber-200/60 inline-block">
                      "{event.trigger}"
                    </p>
                    <p className="text-[11px] text-slate-500 flex items-center gap-1.5">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>{event.created_at ? new Date(event.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently'}</span>
                      <span>·</span>
                      <span className="text-indigo-600 font-medium">{event.action}</span>
                    </p>
                  </div>

                  <button
                    onClick={() => setSelectedEvent(event)}
                    className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-xs transition-all shrink-0 self-start md:self-center flex items-center gap-1.5"
                  >
                    <span>Review & Resolve</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Patient Status Overview Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">Enrolled Patient Recovery Status</h3>
            <Link href="/patients" className="text-xs font-bold text-indigo-600 hover:text-indigo-700">
              View All Directory →
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-y border-slate-100">
                <tr>
                  <th className="p-3">Patient Name</th>
                  <th className="p-3">Procedure</th>
                  <th className="p-3">Countdown</th>
                  <th className="p-3">Phase</th>
                  <th className="p-3">7-Day Adherence</th>
                  <th className="p-3">Safety Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                <tr className="hover:bg-slate-50/50">
                  <td className="p-3 font-bold text-slate-900">Sarah Jenkins</td>
                  <td className="p-3">Knee Surgery</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold">T - 21d</span>
                  </td>
                  <td className="p-3">Pre-Hab</td>
                  <td className="p-3 font-bold text-emerald-600">94.0%</td>
                  <td className="p-3">
                    {criticalCount > 0 ? (
                      <span className="px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-bold">Active Alert</span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold">Safe</span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Safety Resolution Drawer */}
      <SafetyResolutionDrawer
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />
    </div>
  );
}
