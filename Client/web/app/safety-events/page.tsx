'use client';

import React, { useState } from 'react';
import {
  ShieldAlert,
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
  Clock,
  User,
  ArrowRight,
  Filter,
} from 'lucide-react';
import { TopNavbar } from '../../components/TopNavbar';
import { SafetyResolutionDrawer } from '../../components/SafetyResolutionDrawer';
import { useSafetyTriageStore, SafetyEventItem } from '../../stores/useSafetyTriageStore';

export default function SafetyEventsPage() {
  const { events, selectedEvent, setSelectedEvent, activeFilter, setActiveFilter } = useSafetyTriageStore();
  const [statusFilter, setStatusFilter] = useState<'all' | 'open' | 'resolved'>('open');

  // Filter events based on active filters
  const filteredEvents = events.filter((e) => {
    const matchesRisk = activeFilter === 'all' || e.risk_level === activeFilter;
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'open' && e.status !== 'resolved') ||
      (statusFilter === 'resolved' && e.status === 'resolved');
    return matchesRisk && matchesStatus;
  });

  const criticalEvents = filteredEvents.filter((e) => e.risk_level === 'critical');
  const highEvents = filteredEvents.filter((e) => e.risk_level === 'high');
  const mediumEvents = filteredEvents.filter((e) => e.risk_level === 'medium');
  const lowEvents = filteredEvents.filter((e) => e.risk_level === 'low');

  const renderEventCard = (event: SafetyEventItem) => {
    const isResolved = event.status === 'resolved';

    return (
      <div
        key={event.id}
        onClick={() => setSelectedEvent(event)}
        className={`p-4 rounded-2xl border transition-all cursor-pointer shadow-xs hover:shadow-md ${
          isResolved
            ? 'bg-slate-50 border-slate-200 opacity-75'
            : event.risk_level === 'critical'
            ? 'bg-red-50/50 border-red-200 hover:border-red-400'
            : event.risk_level === 'high'
            ? 'bg-orange-50/50 border-orange-200 hover:border-orange-400'
            : event.risk_level === 'medium'
            ? 'bg-amber-50/50 border-amber-200 hover:border-amber-400'
            : 'bg-blue-50/50 border-blue-200 hover:border-blue-400'
        }`}
      >
        <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
          <div className="flex items-center gap-2">
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs font-bold text-slate-900">{event.patient_name || 'Sarah Jenkins'}</span>
          </div>
          {isResolved ? (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Resolved
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-white text-slate-700 border border-slate-200">
              Open
            </span>
          )}
        </div>

        <div className="mt-2.5 space-y-1.5">
          <p className="text-xs font-semibold text-slate-800 italic line-clamp-2 bg-white/80 p-2 rounded-lg border border-slate-200/60">
            "{event.trigger}"
          </p>
          <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
            {event.action}
          </p>
        </div>

        <div className="mt-3 pt-2 border-t border-slate-200/50 flex items-center justify-between text-[10px] text-slate-500">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {event.created_at ? new Date(event.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently'}
          </span>
          <span className="font-bold text-indigo-600 flex items-center gap-0.5">
            Review <ArrowRight className="w-3 h-3" />
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <TopNavbar
        title="Clinical Safety Triage Queue"
        subtitle="4-Tier severity categorization and clinician de-escalation workflow"
      />

      <div className="p-8 space-y-6 max-w-7xl w-full mx-auto">
        {/* Filter Controls */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
          {/* Severity Filters */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mr-2 flex items-center gap-1">
              <Filter className="w-3 h-3" /> Severity:
            </span>
            {[
              { label: 'All', value: 'all' },
              { label: 'Critical', value: 'critical' },
              { label: 'High', value: 'high' },
              { label: 'Medium', value: 'medium' },
              { label: 'Low', value: 'low' },
            ].map((tab) => (
              <button
                key={tab.value}
                onClick={() => setActiveFilter(tab.value as any)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  activeFilter === tab.value
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Status Filters */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mr-2">Status:</span>
            {[
              { label: 'Open Only', value: 'open' },
              { label: 'Resolved', value: 'resolved' },
              { label: 'All', value: 'all' },
            ].map((s) => (
              <button
                key={s.value}
                onClick={() => setStatusFilter(s.value as any)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  statusFilter === s.value
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* 4-Tier Columns Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 items-start">
          {/* Column 1: Critical */}
          <div className="bg-slate-50/70 rounded-2xl p-4 border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-red-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                <h4 className="text-xs font-bold text-red-900 uppercase tracking-wider">1. Critical Crisis</h4>
              </div>
              <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800">
                {criticalEvents.length}
              </span>
            </div>
            <div className="space-y-3">
              {criticalEvents.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">No critical events</p>
              ) : (
                criticalEvents.map(renderEventCard)
              )}
            </div>
          </div>

          {/* Column 2: High */}
          <div className="bg-slate-50/70 rounded-2xl p-4 border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-orange-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
                <h4 className="text-xs font-bold text-orange-900 uppercase tracking-wider">2. Acute Red Flags</h4>
              </div>
              <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-orange-100 text-orange-800">
                {highEvents.length}
              </span>
            </div>
            <div className="space-y-3">
              {highEvents.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">No acute red flags</p>
              ) : (
                highEvents.map(renderEventCard)
              )}
            </div>
          </div>

          {/* Column 3: Medium */}
          <div className="bg-slate-50/70 rounded-2xl p-4 border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-amber-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider">3. Severe Pain</h4>
              </div>
              <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                {mediumEvents.length}
              </span>
            </div>
            <div className="space-y-3">
              {mediumEvents.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">No severe pain alerts</p>
              ) : (
                mediumEvents.map(renderEventCard)
              )}
            </div>
          </div>

          {/* Column 4: Low */}
          <div className="bg-slate-50/70 rounded-2xl p-4 border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-blue-200">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                <h4 className="text-xs font-bold text-blue-900 uppercase tracking-wider">4. Med Decisions</h4>
              </div>
              <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800">
                {lowEvents.length}
              </span>
            </div>
            <div className="space-y-3">
              {lowEvents.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">No medication alerts</p>
              ) : (
                lowEvents.map(renderEventCard)
              )}
            </div>
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
