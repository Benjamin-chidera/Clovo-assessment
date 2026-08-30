'use client';

import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, Phone, X, User, Activity, AlertTriangle } from 'lucide-react';
import { useSafetyTriageStore, SafetyEventItem } from '../stores/useSafetyTriageStore';

const SERVER_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SafetyResolutionDrawerProps {
  event: SafetyEventItem | null;
  onClose: () => void;
}

export const SafetyResolutionDrawer: React.FC<SafetyResolutionDrawerProps> = ({ event, onClose }) => {
  const { resolveEvent } = useSafetyTriageStore();
  const [calledPatient, setCalledPatient] = useState(false);
  const [notifiedSurgeon, setNotifiedSurgeon] = useState(false);
  const [adjustedPlan, setAdjustedPlan] = useState(false);
  const [clinicianNotes, setClinicianNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!event) return null;

  const severityBadge = (level: string) => {
    switch (level) {
      case 'critical':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200">Critical Severity</span>;
      case 'high':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-800 border border-orange-200">High Risk</span>;
      case 'medium':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">Medium Risk</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">Low / Info</span>;
    }
  };

  const handleResolve = async () => {
    setIsSubmitting(true);
    const actionsTaken = [];
    if (calledPatient) actionsTaken.push('Called Patient');
    if (notifiedSurgeon) actionsTaken.push('Notified Lead Surgeon');
    if (adjustedPlan) actionsTaken.push('Adjusted Recovery Plan');

    const fullNotes = [
      actionsTaken.length > 0 ? `Actions: ${actionsTaken.join(', ')}` : '',
      clinicianNotes.trim() ? `Notes: ${clinicianNotes.trim()}` : '',
    ]
      .filter(Boolean)
      .join(' | ') || 'Reviewed and resolved by clinician';

    try {
      await fetch(`${SERVER_URL}/api/admin/safety-events/${event.id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clinician_id: 'clinician_1',
          clinician_name: 'Dr. Sarah Collins',
          clinician_notes: fullNotes,
        }),
      });

      resolveEvent(event.id);
      setIsSubmitting(false);
      onClose();
    } catch (err) {
      console.error('Failed to resolve safety event:', err);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex justify-end z-50 animate-in fade-in duration-150">
      <div className="bg-white w-full max-w-lg h-full shadow-2xl flex flex-col justify-between p-6 border-l border-slate-200 overflow-y-auto">
        {/* Header */}
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center text-red-600">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Safety Event Triage</h3>
                <p className="text-xs text-slate-500 font-medium">Event ID: {event.id.slice(0, 8)}...</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Patient Card */}
          <div className="mt-5 p-4 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs">
                  <User className="w-4 h-4 text-slate-600" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{event.patient_name || 'Sarah Jenkins'}</h4>
                  <p className="text-xs text-slate-500">{event.procedure || 'Knee Surgery'}</p>
                </div>
              </div>
              {severityBadge(event.risk_level)}
            </div>

            <div className="pt-2 border-t border-slate-200/60 grid grid-cols-2 gap-2 text-xs text-slate-600">
              <div>
                <span className="font-semibold text-slate-500">Status:</span>{' '}
                <span className="capitalize font-bold text-slate-800">{event.status}</span>
              </div>
              <div>
                <span className="font-semibold text-slate-500">Detected:</span>{' '}
                <span className="text-slate-800">
                  {event.created_at ? new Date(event.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}
                </span>
              </div>
            </div>
          </div>

          {/* Trigger Utterance */}
          <div className="mt-5 space-y-2">
            <label className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              Patient Utterance / Trigger:
            </label>
            <div className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200/80 text-xs font-medium text-slate-800 leading-relaxed italic">
              "{event.trigger}"
            </div>
          </div>

          {/* Recommended Protocol */}
          <div className="mt-4 space-y-2">
            <label className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-600" />
              Amy's Clinical Guidance & Recommended Action:
            </label>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed">
              {event.action}
            </div>
          </div>

          {/* Clinician Action Checkboxes */}
          {event.status !== 'resolved' && (
            <div className="mt-5 space-y-3">
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Clinician Actions Taken:
              </label>
              <div className="space-y-2">
                <label className="flex items-center gap-2.5 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={calledPatient}
                    onChange={(e) => setCalledPatient(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                  <span>Direct phone contact completed with patient</span>
                </label>
                <label className="flex items-center gap-2.5 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifiedSurgeon}
                    onChange={(e) => setNotifiedSurgeon(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                  <span>Notified lead surgeon / care team</span>
                </label>
                <label className="flex items-center gap-2.5 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={adjustedPlan}
                    onChange={(e) => setAdjustedPlan(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                  <span>Adjusted daily activity instructions</span>
                </label>
              </div>

              <div className="pt-2">
                <label className="block text-xs font-bold text-slate-800 mb-1">
                  Clinician Resolution Notes (Audited):
                </label>
                <textarea
                  value={clinicianNotes}
                  onChange={(e) => setClinicianNotes(e.target.value)}
                  placeholder="e.g. Patient verified resting in safe position. No red-flag symptoms persisting."
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                  rows={2}
                />
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
          >
            Close
          </button>
          {event.status !== 'resolved' ? (
            <button
              onClick={handleResolve}
              disabled={isSubmitting}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm shadow-emerald-200 transition-all flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{isSubmitting ? 'Resolving...' : 'Mark Alert as Resolved'}</span>
            </button>
          ) : (
            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Resolved & Logged</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
