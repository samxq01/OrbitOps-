# OrbitOps — Project Overview

> **Tagline:** Observe. Diagnose. Decide. Recover.
> **Classification:** Educational Satellite Mission Control & Digital Twin Simulator
> **Course:** Software Engineering (IA3 Project)

---

## 1. Executive Summary

**OrbitOps** is an educational, evidence-driven satellite mission operations simulator. It provides operators, software engineering students, and aerospace enthusiasts with an authentic, ground-station-grade control console for managing virtual spacecraft constellations.

Unlike toy satellite trackers that render decorative telemetry or generate random, uncoordinated numbers, OrbitOps introduces a **Causal Satellite Digital Twin**. Subsystem physics—such as solar flux exposure, battery depth of discharge, thermal radiative equilibrium, attitude stability, and downlink signal-to-noise ratio—are coupled through deterministic simulation equations.

When anomalies strike (e.g., thermal runaway, solar array shadow during eclipse, transponder failure, or sensor disagreement), operators do not guess: they employ **Evidence-Based Fault Investigation**, evaluating competing root cause hypotheses with supporting and refuting telemetry proofs.

---

## 2. Core Innovations

### Innovation A — Causal Satellite Digital Twin
Subsystems are physically and logically coupled:
- **Power Subsystem:** Solar array irradiance, battery state-of-charge, bus voltage, and subsystem load balancing.
- **Thermal Subsystem:** Solar absorptivity, internal component dissipation, space radiative cooling, and heater actuation.
- **Attitude Determination and Control System (ADCS):** Reaction wheel momentum, magnetorquer unloading, sun-pointing vs. ground-pointing modes.
- **Communications Subsystem:** RF carrier frequency, transmitter power, receiver gain, Doppler shift, and ground station line-of-sight geometry.
- **Payload Subsystem:** Optical/radar sensor activation, power/thermal load profiles, data storage buffers, and transmission downlinks.

### Innovation B — Evidence-Based Fault Investigation
Operators investigate anomalies through an aerospace-grade incident engine:
- Deterministic symptom detection across telemetry parameters.
- Hypothesis generation with verifiable criteria (supporting vs. contradicting evidence).
- Diagnosis confidence scoring (never stating certainty without sufficient corroboration).
- Validated recovery procedures (e.g., shedding non-critical payload loads before battery voltage drops below critical bus threshold).

### Innovation C — Safety-Aware Satellite Command Execution
Commands to virtual satellites must undergo a multi-stage validation pipeline:
1. **QUEUED:** Telecommand packet assembled in ground queue.
2. **VALIDATING:** Verification of operational preconditions (e.g., ground contact window open, satellite not in safemode, sufficient battery margin).
3. **APPROVED / REJECTED:** Strict gatekeeping preventing catastrophic commands.
4. **EXECUTING:** Telecommand uplinked and acknowledged by spacecraft onboard computer.
5. **COMPLETED / FAILED:** Subsystem response monitored and confirmed.

### Innovation D — Mission Time Machine & Event Replay
Complete mission states, telemetry histories, ground passes, and incident chronologies are recorded in an append-only event log. Operators can jump back to inspect historical anomalies without corrupting active simulation state.

### Innovation E — Reproducible Emergency Scenarios
Preconfigured mission scenarios provide deterministic baselines for training and evaluation:
- *Scenario Alpha: Solar Eclipse Power Crisis*
- *Scenario Bravo: Communication Blackout & Desynchronization*
- *Scenario Charlie: Radiative Heat Shield Degradation*
- *Scenario Delta: Conflicting Horizon Sensor Readings*

---

## 3. Strict Simulation Boundary

> [!IMPORTANT]
> OrbitOps is an educational simulation environment. All telemetry feeds, orbital mechanics calculations, attitude models, fault injections, and telecommands are simulated within the local runtime. No connections to live spacecraft or operational orbital networks are established.
