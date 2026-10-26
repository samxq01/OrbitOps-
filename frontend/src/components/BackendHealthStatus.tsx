"use client";

import React from "react";
import { Server, RefreshCw, CheckCircle2, AlertCircle, ShieldCheck, WifiOff } from "lucide-react";
import { BackendCheckResult } from "@/lib/api";

interface BackendHealthStatusProps {
  backendHealth: BackendCheckResult | null;
  loading: boolean;
  onRefresh: () => void;
}

export function BackendHealthStatus({
  backendHealth,
  loading,
  onRefresh,
}: BackendHealthStatusProps) {
  const isHealthy = backendHealth?.ok;
  const data = backendHealth?.data;

  return (
    <div className="bg-[#111C2E] border border-[#1E3352] rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between pb-4 border-b border-[#1E3352]">
        <div className="flex items-center space-x-3">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center ${
              isHealthy
                ? "bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/30"
                : "bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/30"
            }`}
          >
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white tracking-wide">
              Backend Telemetry & Simulation Service
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              FastAPI Core • Single Authoritative State Source
            </p>
          </div>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#18263B] hover:bg-[#1E3352] text-[#42C8FF] text-xs font-mono border border-[#42C8FF]/20 transition-all disabled:opacity-50 cursor-pointer"
          title="Query GET /api/v1/health"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>{loading ? "CHECKING..." : "PING API"}</span>
        </button>
      </div>

      <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="bg-[#080F1D] p-3 rounded-lg border border-[#1E3352]">
          <span className="text-slate-400 block text-[10px] uppercase">Service ID</span>
          <span className="font-semibold text-white mt-1 block">
            {data?.service || "orbitops-api"}
          </span>
        </div>

        <div className="bg-[#080F1D] p-3 rounded-lg border border-[#1E3352]">
          <span className="text-slate-400 block text-[10px] uppercase">Health Status</span>
          <div className="flex items-center space-x-1.5 mt-1">
            {isHealthy ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-[#22C55E]" />
                <span className="font-bold text-[#22C55E] uppercase">{data?.status}</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-[#EF4444]" />
                <span className="font-bold text-[#EF4444] uppercase">DISCONNECTED</span>
              </>
            )}
          </div>
        </div>

        <div className="bg-[#080F1D] p-3 rounded-lg border border-[#1E3352]">
          <span className="text-slate-400 block text-[10px] uppercase">Roundtrip Latency</span>
          <span className="font-semibold text-[#42C8FF] mt-1 block">
            {backendHealth ? `${backendHealth.latencyMs} ms` : "---"}
          </span>
        </div>

        <div className="bg-[#080F1D] p-3 rounded-lg border border-[#1E3352]">
          <span className="text-slate-400 block text-[10px] uppercase">Simulation Mode</span>
          <div className="flex items-center space-x-1.5 mt-1">
            <ShieldCheck className="w-3.5 h-3.5 text-[#729CFF]" />
            <span className="font-semibold text-[#729CFF]">
              {data?.simulation_mode ? "ACTIVE" : "INACTIVE"}
            </span>
          </div>
        </div>
      </div>

      {/* Disconnection Warning Message */}
      {!isHealthy && !loading && (
        <div className="mt-4 p-3 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/30 flex items-start space-x-3 text-xs">
          <WifiOff className="w-4 h-4 text-[#EF4444] mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold text-[#EF4444]">Cannot connect to OrbitOps Backend API</p>
            <p className="text-slate-300 text-[11px] mt-1">
              Ensure the FastAPI backend is running locally on port 8000:
            </p>
            <code className="inline-block mt-1 px-2 py-1 bg-[#080F1D] text-[#42C8FF] rounded text-[11px] font-mono border border-slate-700">
              cd backend &amp;&amp; uv run uvicorn app.main:app --reload --port 8000
            </code>
            {backendHealth?.error && (
              <p className="text-slate-400 text-[10px] mt-1 font-mono">
                Error details: {backendHealth.error}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
