'use client';

import React, { useEffect } from 'react';
import './globals.css';
import { Sidebar } from '../components/Sidebar';
import { AccessJustificationModal } from '../components/AccessJustificationModal';
import { adminSocket } from '../services/adminSocket';
import { useSafetyTriageStore } from '../stores/useSafetyTriageStore';

const SERVER_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { setEvents } = useSafetyTriageStore();

  useEffect(() => {
    // 1. Initialize real-time Socket.IO connection
    adminSocket.connect();

    // 2. Fetch initial safety events from backend
    const fetchInitialData = async () => {
      try {
        const res = await fetch(`${SERVER_URL}/api/admin/safety-events`);
        if (res.ok) {
          const data = await res.json();
          setEvents(data);
        }
      } catch (err) {
        console.warn('Initial safety events fetch failed:', err);
      }
    };

    fetchInitialData();

    return () => {
      adminSocket.disconnect();
    };
  }, [setEvents]);

  return (
    <html lang="en">
      <head>
        <title>Clovo Clinician Portal — AI Recovery Coach Oversight</title>
        <meta name="description" content="Clinical safety triage, conversation audit, and patient oversight dashboard for Clovo." />
      </head>
      <body className="bg-[#F8F9FD] text-slate-900 flex min-h-screen">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {children}
        </main>
        <AccessJustificationModal />
      </body>
    </html>
  );
}
