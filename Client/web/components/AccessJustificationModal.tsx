'use client';

import React, { useState } from 'react';
import { Lock, ShieldAlert, X, FileText } from 'lucide-react';
import { useAuditStore } from '../stores/useAuditStore';

export const AccessJustificationModal: React.FC = () => {
  const {
    isAccessModalOpen,
    pendingPatientName,
    pendingConversationId,
    closeAccessModal,
    onAccessGrantedCallback,
    logAuditAccess,
  } = useAuditStore();

  const [selectedReason, setSelectedReason] = useState<string>('Routine Pre-Op Physiotherapy Review');
  const [customNote, setCustomNote] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  if (!isAccessModalOpen) return null;

  const reasons = [
    'Routine Pre-Op Physiotherapy Review',
    'Patient Direct Telephone / Clinic Inquiry',
    'Safety Alert & Symptom Escalation Follow-Up',
    'Scheduled Clinical Quality Assurance (QA) Audit',
    'Multidisciplinary Team (MDT) Surgical Case Review',
  ];

  const handleConfirm = async () => {
    setIsSubmitting(true);
    const finalReason = customNote.trim() ? `${selectedReason}: ${customNote.trim()}` : selectedReason;

    await logAuditAccess(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000', {
      action: 'VIEW_CONVERSATION',
      conversation_id: pendingConversationId || undefined,
      access_reason: finalReason,
    });

    if (onAccessGrantedCallback) {
      onAccessGrantedCallback(finalReason);
    }

    setIsSubmitting(false);
    closeAccessModal();
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Clinical Access Justification</h3>
              <p className="text-xs text-slate-500 font-medium">HIPAA / GDPR / NHS DTAC Compliance Gate</p>
            </div>
          </div>
          <button
            onClick={closeAccessModal}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="py-4 space-y-4">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs text-slate-700 space-y-1">
            <p>
              You are opening the private AI recovery coaching thread for{' '}
              <strong className="text-slate-900">{pendingPatientName || 'Patient'}</strong>.
            </p>
            <p className="text-slate-500">
              Per the <em>Need-to-Know Principle</em>, every access is permanently logged in the immutable clinical audit trail.
            </p>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-800 mb-2">Select Clinical Reason for Access:</label>
            <div className="space-y-2">
              {reasons.map((r) => (
                <label
                  key={r}
                  className={`flex items-center gap-3 p-2.5 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${
                    selectedReason === r
                      ? 'bg-indigo-50 border-indigo-300 text-indigo-900 shadow-xs'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="clinicalReason"
                    value={r}
                    checked={selectedReason === r}
                    onChange={() => setSelectedReason(r)}
                    className="text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>{r}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-800 mb-1">Additional Clinical Notes (Optional):</label>
            <textarea
              value={customNote}
              onChange={(e) => setCustomNote(e.target.value)}
              placeholder="e.g. Phone consultation with patient regarding pre-op mobility questions"
              className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              rows={2}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2.5">
          <button
            onClick={closeAccessModal}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={isSubmitting}
            className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm shadow-indigo-200 transition-all flex items-center gap-1.5"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>{isSubmitting ? 'Logging Access...' : 'Confirm Access & View'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
