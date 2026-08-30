import { create } from 'zustand';

export interface ClinicianProfile {
  id: string;
  name: string;
  role: string;
  department: string;
  hospital: string;
}

interface AuthState {
  clinician: ClinicianProfile;
  setClinician: (clinician: ClinicianProfile) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  clinician: {
    id: 'clinician_1',
    name: 'Dr. Sarah Collins, FRCS',
    role: 'Lead Recovery Clinician',
    department: 'Orthopaedic Surgery',
    hospital: 'St. Thomas NHS Trust',
  },
  setClinician: (clinician) => set({ clinician }),
}));
