"use client";

import React from "react";
import {
  GitBranch,
  Shield,
  Cpu,
  Activity,
  Layers,
  CheckCircle,
  Clock,
  Compass,
} from "lucide-react";
import { BackendCheckResult } from "@/lib/api";
import { BackendHealthStatus } from "./BackendHealthStatus";

interface PhaseItem {
  id: string;
  name: string;
  status: "completed" | "in_progress" | "planned";
  summary: string;
}

const phases: PhaseItem[] = [
  {
    id: "00",
    name: "Repository Initialization and Foundation",
    status: "completed",
    summary: "Monorepo structure, FastAPI health check, Next.js dark console, toolchain, AGENTS contract.",
  },
  {
    id: "01",
    name: "Requirements, SRS, Architecture, UML Baseline",
    status: "planned",
    summary: "IEEE 830 SRS, 5 UML diagrams (Use Case, Class, Sequence, Activity, State Machine).",
  },
  {
    id: "02",
    name: "Satellite Domain Models and Database",
    status: "planned",
    summary: "SQLAlchemy models, SQLite persistence, satellite registry, subsystem entities.",
  },
  {
    id: "03",
    name: "Deterministic Satellite Digital Twin Engine",
    status: "planned",
    summary: "Coupled differential equations (Power, Thermal, ADCS, Comms, Payload) & tick engine.",
  },
  {
    id: "04",
    name: "REST APIs and Real-Time Telemetry Streaming",
    status: "planned",
    summary: "WebSockets, high-frequency telemetry broadcast, REST controls, SSE channels.",
  },
  {
    id: "05",
    name: "Professional Mission Control Dashboard",
    status: "planned",
    summary: "Multi-satellite overview, subsystem telemetry gauges, alert tickers, operational panels.",
  },
  {
    id: "06",
    name: "Interactive 3D Earth and Orbital Visualization",
    status: "planned",
    summary: "Three.js / React Three Fiber globe, satellite orbit path rendering, terminator lighting.",
  },
  {
    id: "07",
    name: "Fault Injection and Emergency Scenarios",
    status: "planned",
    summary: "Solar eclipse, comms blackout, thermal degradation, gyro drift scenarios.",
  },
  {
    id: "08",
    name: "Evidence-Based Anomaly Investigator",
    status: "planned",
    summary: "Hypothesis evaluator, supporting/counter evidence matrix, confidence scorer.",
  },
  {
    id: "09",
    name: "Ground Station Communication & Contact Windows",
    status: "planned",
    summary: "Pass scheduler, line-of-sight geometry, RF link budget, Doppler calculation.",
  },
  {
    id: "10",
    name: "Safety-Aware Satellite Command Console",
    status: "planned",
    summary: "Multi-stage validation pipeline (QUEUED -> VALIDATING -> APPROVED -> EXECUTING).",
  },
  {
    id: "11",
    name: "Mission Time Machine and Event Replay",
    status: "planned",
    summary: "Append-only mission log, scrubbable timeline, historical incident inspection.",
  },
  {
    id: "12",
    name: "Reports, Analytics, and Export",
    status: "planned",
    summary: "Incident debrief generator, post-mortem PDF/JSON exporter, telemetry trend analysis.",
  },
  {
    id: "13",
    name: "What-If Recovery Simulation",
    status: "planned",
    summary: "Branching sandbox for evaluating recovery procedures before live uplink.",
  },
  {
    id: "14",
    name: "Full Integration, Security, and Testing",
    status: "planned",
    summary: "End-to-end integration tests, Playwright browser test suite, security hardening.",
  },
  {
    id: "15",
    name: "Final Documentation, IA3 Deliverables, and Release",
    status: "planned",
    summary: "Final SRS/UML synchronization, comprehensive test report, GitHub release tag.",
  },
];

export function OverviewDashboard({
  backendHealth,
  loading,
  onRefresh,
}: {
  backendHealth: BackendCheckResult | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  return (
    <div className="space-y-6 pb-12">
      {/* Hero Welcome Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#111C2E] via-[#18263B] to-[#111C2E] border border-[#1E3352] p-6 shadow-2xl">
        <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-[#42C8FF]/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-wider rounded-full bg-[#42C8FF]/10 text-[#42C8FF] border border-[#42C8FF]/30">
                Software Engineering IA3
              </span>
              <span className="px-2.5 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-wider rounded-full bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/30">
                Phase 00 Foundation Ready
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
              OrbitOps Console
            </h1>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
              Evidence-driven satellite mission operations console &amp; causal digital twin simulator.
              Designed for deterministic anomaly investigation, safe telecommands, and mission time machine replay.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <div className="bg-[#080F1D]/80 backdrop-blur border border-[#1E3352] px-4 py-2.5 rounded-xl font-mono text-xs">
              <div className="text-slate-400 text-[10px] uppercase">Active Branch</div>
              <div className="text-[#42C8FF] font-semibold flex items-center space-x-1.5 mt-0.5">
                <GitBranch className="w-3.5 h-3.5" />
                <span>feature/orbitops-ia3</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Backend Health Check Panel */}
      <BackendHealthStatus
        backendHealth={backendHealth}
        loading={loading}
        onRefresh={onRefresh}
      />

      {/* Innovation Pillars Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-white tracking-wide flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[#42C8FF]" />
            <span>Core Architectural Innovations</span>
          </h2>
          <span className="text-xs font-mono text-slate-400">
            Authoritative Simulator Design
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#111C2E] border border-[#1E3352] rounded-xl p-4 flex flex-col justify-between hover:border-[#42C8FF]/40 transition-colors">
            <div>
              <div className="w-8 h-8 rounded-lg bg-[#42C8FF]/10 text-[#42C8FF] flex items-center justify-center mb-3">
                <Cpu className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                A. Causal Digital Twin
              </h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Tightly coupled physics across Power, Thermal, ADCS, Comms, and Payload. Solar eclipses cause battery drain, driving temperature changes and safe-mode transitions.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#1E3352] text-[10px] font-mono text-slate-400">
              Module: <span className="text-[#729CFF]">Digital Twin Engine</span>
            </div>
          </div>

          <div className="bg-[#111C2E] border border-[#1E3352] rounded-xl p-4 flex flex-col justify-between hover:border-[#729CFF]/40 transition-colors">
            <div>
              <div className="w-8 h-8 rounded-lg bg-[#729CFF]/10 text-[#729CFF] flex items-center justify-center mb-3">
                <Activity className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                B. Evidence-Based Diagnosis
              </h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Deterministic telemetry anomaly analysis. Evaluates candidate root causes with supporting vs. contradicting evidence matrices and calibrated confidence scores.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#1E3352] text-[10px] font-mono text-slate-400">
              Module: <span className="text-[#729CFF]">Anomaly Investigator</span>
            </div>
          </div>

          <div className="bg-[#111C2E] border border-[#22C55E]/40 rounded-xl p-4 flex flex-col justify-between hover:border-[#22C55E]/40 transition-colors">
            <div>
              <div className="w-8 h-8 rounded-lg bg-[#22C55E]/10 text-[#22C55E] flex items-center justify-center mb-3">
                <Shield className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                C. Safe Satellite Commands
              </h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Precondition validation pipeline. Commands progress strictly through QUEUED &rarr; VALIDATING &rarr; APPROVED &rarr; EXECUTING with ground-contact interlocking.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#1E3352] text-[10px] font-mono text-slate-400">
              Module: <span className="text-[#729CFF]">Command Validator</span>
            </div>
          </div>

          <div className="bg-[#111C2E] border border-[#1E3352] rounded-xl p-4 flex flex-col justify-between hover:border-[#F59E0B]/40 transition-colors">
            <div>
              <div className="w-8 h-8 rounded-lg bg-[#F59E0B]/10 text-[#F59E0B] flex items-center justify-center mb-3">
                <Clock className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                D. Mission Time Machine
              </h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Append-only event log and scrubbable timeline. Allows operators to rewind, re-inspect anomalies, and evaluate alternative recovery decisions safely.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#1E3352] text-[10px] font-mono text-slate-400">
              Module: <span className="text-[#729CFF]">Event Replay Engine</span>
            </div>
          </div>
        </div>
      </div>

      {/* Master 16-Phase Roadmap Section */}
      <div className="bg-[#111C2E] border border-[#1E3352] rounded-xl p-5">
        <div className="flex items-center justify-between pb-4 border-b border-[#1E3352]">
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center space-x-2">
              <Compass className="w-4 h-4 text-[#42C8FF]" />
              <span>Engineering Execution Roadmap (16 Phases)</span>
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Disciplined incremental development with verified Git feature checkpoints
            </p>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded bg-[#080F1D] text-[#42C8FF] border border-[#1E3352]">
            Phase 00 of 15
          </span>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          {phases.map((p) => {
            const isDone = p.status === "completed";
            return (
              <div
                key={p.id}
                className={`p-3 rounded-lg border flex items-start space-x-3 transition-colors ${
                  isDone
                    ? "bg-[#18263B]/80 border-[#22C55E]/40"
                    : "bg-[#080F1D]/60 border-[#1E3352] opacity-75"
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isDone ? (
                    <CheckCircle className="w-4 h-4 text-[#22C55E]" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-600 flex items-center justify-center text-[9px] font-mono text-slate-400">
                      {p.id}
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-semibold ${isDone ? "text-white" : "text-slate-300"}`}>
                      Phase {p.id} — {p.name}
                    </span>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase ml-2 ${
                        isDone
                          ? "bg-[#22C55E]/10 text-[#22C55E] border-[#22C55E]/30"
                          : "bg-[#111C2E] text-slate-400 border-slate-700"
                      }`}
                    >
                      {p.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-normal">
                    {p.summary}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
