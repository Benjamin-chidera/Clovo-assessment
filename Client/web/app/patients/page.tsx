'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Users, Search, ShieldAlert, CheckCircle2, MessageSquare, Flame } from 'lucide-react';
import { TopNavbar } from '../../components/TopNavbar';
import { useAuditStore } from '../../stores/useAuditStore';

const SERVER_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PatientItem {
  id: number;
  name: string;
  procedure: string;
  procedure_date: string | null;
  days_away: number | null;
  phase: string;
  adherence: number;
  highest_risk: string;
  open_alerts_count: number;
}

export default function PatientsPage() {
  const router = useRouter();
  const { openAccessModal } = useAuditStore();
  const [patients, setPatients] = useState<PatientItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await fetch(`${SERVER_URL}/api/admin/patients`);
        if (res.ok) {
          const data = await res.json();
          setPatients(data);
        }
      } catch (err) {
        console.error('Failed to load patients:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPatients();
  }, []);

  const filteredPatients = patients.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.procedure.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAuditClick = (patient: PatientItem) => {
    openAccessModal('conv-1', patient.name, (reason) => {
      router.push('/conversations');
    });
  };

  const riskBadge = (risk: string, openAlerts: number) => {
    if (openAlerts > 0) {
      return (
        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200 flex items-center gap-1">
          <ShieldAlert className="w-3 h-3 text-red-600" />
          {openAlerts} Active Alert{openAlerts > 1 ? 's' : ''}
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
        Safe
      </span>
    );
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <TopNavbar
        title="Enrolled Patient Directory"
        subtitle="Longitudinal recovery status, surgery countdowns, and adherence tracking"
      />

      <div className="p-8 space-y-6 max-w-7xl w-full mx-auto">
        {/* Search & Header Controls */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by patient name or procedure..."
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 text-xs bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="text-xs text-slate-500 font-semibold">
            Showing <strong className="text-slate-900">{filteredPatients.length}</strong> enrolled patient
            {filteredPatients.length === 1 ? '' : 's'}
          </div>
        </div>

        {/* Patients Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                <tr>
                  <th className="p-4">Patient Name</th>
                  <th className="p-4">Procedure</th>
                  <th className="p-4">Surgery Countdown</th>
                  <th className="p-4">Care Phase</th>
                  <th className="p-4">7-Day Adherence</th>
                  <th className="p-4">Safety Status</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400">
                      Loading patient directory...
                    </td>
                  </tr>
                ) : filteredPatients.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400">
                      No patients found matching your search.
                    </td>
                  </tr>
                ) : (
                  filteredPatients.map((patient) => (
                    <tr key={patient.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="p-4 font-bold text-slate-900 flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs">
                          {patient.name[0]}
                        </div>
                        <span>{patient.name}</span>
                      </td>
                      <td className="p-4 font-semibold text-slate-800">{patient.procedure}</td>
                      <td className="p-4">
                        <span className="px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 font-bold border border-indigo-200/60">
                          {patient.days_away !== null ? `T - ${patient.days_away}d` : 'T - 21d'}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[11px] font-semibold">
                          {patient.phase}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="text-emerald-600 font-bold flex items-center gap-1">
                          <Flame className="w-3.5 h-3.5 text-orange-500" />
                          {patient.adherence}%
                        </span>
                      </td>
                      <td className="p-4">{riskBadge(patient.highest_risk, patient.open_alerts_count)}</td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => handleAuditClick(patient)}
                          className="px-3.5 py-1.5 rounded-xl bg-slate-100 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 text-xs font-bold transition-all border border-slate-200/80 inline-flex items-center gap-1.5"
                        >
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>Audit Chat</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
