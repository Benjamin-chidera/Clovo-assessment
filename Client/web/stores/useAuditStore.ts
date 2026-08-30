import { create } from 'zustand';

export interface AuditEntry {
  id?: string;
  user_id: string;
  user_name: string;
  user_role: string;
  action: string;
  patient_id?: number;
  conversation_id?: string;
  access_reason: string;
  created_at?: string;
}

interface AuditState {
  isAccessModalOpen: boolean;
  pendingConversationId: string | null;
  pendingPatientName: string | null;
  onAccessGrantedCallback: ((reason: string) => void) | null;
  openAccessModal: (
    conversationId: string,
    patientName: string,
    onGranted: (reason: string) => void
  ) => void;
  closeAccessModal: () => void;
  logAuditAccess: (
    apiUrl: string,
    entry: {
      action: string;
      patient_id?: number;
      conversation_id?: string;
      access_reason: string;
    }
  ) => Promise<void>;
}

export const useAuditStore = create<AuditState>((set) => ({
  isAccessModalOpen: false,
  pendingConversationId: null,
  pendingPatientName: null,
  onAccessGrantedCallback: null,

  openAccessModal: (conversationId, patientName, onGranted) =>
    set({
      isAccessModalOpen: true,
      pendingConversationId: conversationId,
      pendingPatientName: patientName,
      onAccessGrantedCallback: onGranted,
    }),

  closeAccessModal: () =>
    set({
      isAccessModalOpen: false,
      pendingConversationId: null,
      pendingPatientName: null,
      onAccessGrantedCallback: null,
    }),

  logAuditAccess: async (apiUrl, entry) => {
    try {
      await fetch(`${apiUrl}/api/admin/audit-logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'clinician_1',
          user_name: 'Dr. Sarah Collins',
          user_role: 'clinician',
          ...entry,
        }),
      });
    } catch (err) {
      console.warn('Could not record audit log:', err);
    }
  },
}));
