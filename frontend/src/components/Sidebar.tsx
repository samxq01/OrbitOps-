"use client";

import React from "react";
import {
  Satellite,
  Compass,
  Activity,
  AlertTriangle,
  Terminal,
  Radio,
  Sliders,
  History,
  BarChart3,
  Settings,
  ShieldAlert,
  Layers,
} from "lucide-react";

interface NavItem {
  name: string;
  phase: string;
  icon: React.ComponentType<{ className?: string }>;
  active?: boolean;
}

const navItems: NavItem[] = [
  { name: "Mission Overview", phase: "Active", icon: Layers, active: true },
  { name: "Satellite Fleet", phase: "Phase 02", icon: Satellite },
  { name: "Orbital 3D Viewer", phase: "Phase 06", icon: Compass },
  { name: "Live Telemetry", phase: "Phase 04", icon: Activity },
  { name: "Incident Center", phase: "Phase 08", icon: AlertTriangle },
  { name: "Command Console", phase: "Phase 10", icon: Terminal },
  { name: "Ground Stations", phase: "Phase 09", icon: Radio },
  { name: "Scenario Studio", phase: "Phase 07", icon: Sliders },
  { name: "Mission Replay", phase: "Phase 11", icon: History },
  { name: "Analytics & Reports", phase: "Phase 12", icon: BarChart3 },
  { name: "Settings", phase: "Roadmap", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-[#111C2E] border-r border-[#1E3352] flex flex-col justify-between select-none">
      <div>
        {/* Branding */}
        <div className="p-5 border-b border-[#1E3352]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#42C8FF] to-[#729CFF] flex items-center justify-center shadow-lg shadow-[#42C8FF]/20">
              <Satellite className="w-6 h-6 text-[#080F1D]" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-lg tracking-wider text-white">ORBIT</span>
                <span className="font-bold text-lg tracking-wider text-[#42C8FF]">OPS</span>
              </div>
              <p className="text-[10px] tracking-widest text-[#729CFF] font-semibold uppercase">
                Digital Twin Sim
              </p>
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-2 font-mono">
            Observe • Diagnose • Decide • Recover
          </p>
        </div>

        {/* Navigation list */}
        <nav className="p-3 space-y-1">
          <p className="px-3 py-2 text-[10px] font-mono tracking-widest text-slate-400 uppercase">
            Operations Console
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.name}
                className={`flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-all ${
                  item.active
                    ? "bg-[#18263B] text-[#42C8FF] border border-[#42C8FF]/30 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#18263B]/50 cursor-not-allowed opacity-75"
                }`}
                title={item.active ? "Current active module" : `Scheduled for ${item.phase}`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={`w-4 h-4 ${item.active ? "text-[#42C8FF]" : "text-slate-500"}`} />
                  <span>{item.name}</span>
                </div>
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                    item.active
                      ? "bg-[#42C8FF]/10 text-[#42C8FF] border-[#42C8FF]/30"
                      : "bg-[#080F1D] text-slate-500 border-slate-700"
                  }`}
                >
                  {item.phase}
                </span>
              </div>
            );
          })}
        </nav>
      </div>

      {/* Safety & Environment Notice */}
      <div className="p-3 border-t border-[#1E3352] bg-[#0B1424]">
        <div className="flex items-center space-x-2 text-[#F59E0B] text-[11px] font-medium">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>SIMULATION MODE</span>
        </div>
        <p className="text-[10px] text-slate-400 mt-1 font-mono leading-tight">
          Phase 00 Foundation. Telemetry is purely simulated.
        </p>
      </div>
    </aside>
  );
}
