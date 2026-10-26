"use client";

import React, { useState, useEffect } from "react";
import { Clock, ShieldAlert, Cpu } from "lucide-react";
import { BackendCheckResult } from "@/lib/api";

interface HeaderProps {
  backendHealth: BackendCheckResult | null;
  loading: boolean;
}

export function Header({ backendHealth, loading }: HeaderProps) {
  const [utcTime, setUtcTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-[#111C2E] border-b border-[#1E3352] flex flex-col">
      {/* Prominent Simulation Indicator Strip */}
      <div className="bg-[#18263B] border-b border-[#1E3352] px-4 py-1.5 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center space-x-2 text-[#F59E0B]">
          <ShieldAlert className="w-3.5 h-3.5 animate-pulse" />
          <span className="font-semibold uppercase tracking-wider text-[11px]">
            SIMULATION ENVIRONMENT ONLY
          </span>
          <span className="text-slate-400 hidden md:inline text-[11px]">
            — All spacecraft telemetry, orbital dynamics, and faults are simulated for training.
          </span>
        </div>
        <div className="flex items-center space-x-4 text-slate-300 text-[11px]">
          <span className="text-slate-400">MISSION:</span>
          <span className="text-[#42C8FF] font-bold">ORBITOPS-TRAINING-01</span>
        </div>
      </div>

      {/* Main Top Bar */}
      <div className="px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-2.5 w-2.5 rounded-full bg-[#42C8FF] animate-ping" />
          <span className="text-sm font-semibold tracking-wide text-white">
            MISSION OPERATIONS COMMAND CENTER
          </span>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#18263B] text-[#729CFF] border border-[#729CFF]/30">
            PHASE 00
          </span>
        </div>

        <div className="flex items-center space-x-6 text-xs font-mono">
          {/* UTC Clock */}
          <div className="flex items-center space-x-2 text-slate-300 bg-[#080F1D] px-3 py-1.5 rounded border border-[#1E3352]">
            <Clock className="w-3.5 h-3.5 text-[#42C8FF]" />
            <span className="text-slate-400">UTC:</span>
            <span className="text-white font-medium">{utcTime || "SYNCING..."}</span>
          </div>

          {/* Backend Connection Indicator */}
          <div
            className={`flex items-center space-x-2 px-3 py-1.5 rounded border ${
              loading
                ? "bg-[#18263B] border-slate-600 text-slate-300"
                : backendHealth?.ok
                ? "bg-[#22C55E]/10 border-[#22C55E]/40 text-[#22C55E]"
                : "bg-[#EF4444]/10 border-[#EF4444]/40 text-[#EF4444]"
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span className="text-slate-400">API:</span>
            <span className="font-semibold">
              {loading
                ? "CHECKING..."
                : backendHealth?.ok
                ? `ONLINE (${backendHealth.latencyMs}ms)`
                : "OFFLINE"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
