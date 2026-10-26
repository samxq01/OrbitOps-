"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { OverviewDashboard } from "@/components/OverviewDashboard";
import { fetchBackendHealth, BackendCheckResult } from "@/lib/api";

export default function Home() {
  const [backendHealth, setBackendHealth] = useState<BackendCheckResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const checkHealth = useCallback(async () => {
    try {
      const result = await fetchBackendHealth();
      setBackendHealth(result);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleManualRefresh = useCallback(() => {
    setLoading(true);
    checkHealth();
  }, [checkHealth]);

  useEffect(() => {
    let isMounted = true;
    fetchBackendHealth().then((result) => {
      if (isMounted) {
        setBackendHealth(result);
        setLoading(false);
      }
    });

    const interval = setInterval(() => {
      fetchBackendHealth().then((result) => {
        if (isMounted) {
          setBackendHealth(result);
        }
      });
    }, 15000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex h-screen w-full bg-[#080F1D] text-slate-100 overflow-hidden font-sans">
      {/* Fixed Left Navigation Console */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Operations Header & Simulation Banner */}
        <Header backendHealth={backendHealth} loading={loading} />

        {/* Scrollable Dashboard Workspace */}
        <main className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar">
          <OverviewDashboard
            backendHealth={backendHealth}
            loading={loading}
            onRefresh={handleManualRefresh}
          />
        </main>
      </div>
    </div>
  );
}
