# OrbitOps — Requirements Traceability Matrix (RTM)

**Specification Baseline:** `ORBITOPS-SRS-V1.0`
**Current Milestone:** Phase 02 (Satellite Domain Models, Database & Persistence Engine)

---

## 1. Traceability Matrix

| Req ID | Requirement Summary | Priority | Responsible Component | Related UML | Planned Test Case | Target Phase | Implementation Status |
|---|---|---|---|---|---|---|---|
| **FR-001** | Multi-satellite registry (Alpha, Beta, Gamma) | High | `backend/app/repositories/satellite_repository.py` | `02-class` | `TC-01` | Phase 02 | **IMPLEMENTED** |
| **FR-002** | Satellite operational mode query | High | `backend/app/models/satellite.py` | `05-state-machine` | `TC-02` | Phase 02 | **IMPLEMENTED** |
| **FR-003** | Configurable spacecraft physical constants | Medium| `backend/app/models/satellite.py` | `02-class` | `TC-03` | Phase 02 | **IMPLEMENTED** |
| **FR-004** | Discrete simulation tick integration ($\Delta t=1\text{s}$) | High | `backend/domain/engine.py` | `02-class` | `TC-04` | Phase 03 | **PLANNED** |
| **FR-005** | Simulation clock controls (pause, warp, step)| High | `backend/domain/clock.py` | `01-use-case` | `TC-05` | Phase 03 | **PLANNED** |
| **FR-006** | Orbital propagation & eclipse calculation | High | `backend/domain/orbit.py` | `02-class` | `TC-06` | Phase 03 | **PLANNED** |
| **FR-007** | Coupled subsystem telemetry generation | High | `backend/domain/subsystems/` | `02-class` | `TC-07` | Phase 03 | **PLANNED** |
| **FR-008** | Real-time telemetry WebSocket streaming | High | `backend/api/v1/telemetry.py` | `01-use-case` | `TC-08` | Phase 04 | **PLANNED** |
| **FR-009** | Telemetry samples database persistence | High | `backend/app/repositories/telemetry_repository.py`| `02-class` | `TC-09` | Phase 02 | **IMPLEMENTED** |
| **FR-010** | Multi-tier threshold evaluation (Nom/Warn/Crit)| High| `backend/domain/detector.py` | `04-activity` | `TC-10` | Phase 05 | **PLANNED** |
| **FR-011** | Aggregated dashboard health indicators | High | `frontend/components/Health/` | `01-use-case` | `TC-11` | Phase 05 | **PLANNED** |
| **FR-012** | Autonomous emergency safe-mode transition | High | `backend/domain/satellite.py` | `05-state-machine` | `TC-12` | Phase 03 | **PLANNED** |
| **FR-013** | Interactive 3D Earth globe with terminator | Medium| `frontend/components/Orbit3D/`| `01-use-case` | `TC-13` | Phase 06 | **PLANNED** |
| **FR-014** | Orbital trajectory and ground track rendering | Medium| `frontend/components/Orbit3D/`| `01-use-case` | `TC-14` | Phase 06 | **PLANNED** |
| **FR-015** | Ground station visibility cones visualization| Low | `frontend/components/Orbit3D/`| `01-use-case` | `TC-15` | Phase 06 | **PLANNED** |
| **FR-016** | Catalog of 4 mandatory emergency scenarios | High | `backend/domain/scenarios/` | `02-class` | `TC-16` | Phase 07 | **PLANNED** |
| **FR-017** | Scheduled and state-conditional fault triggers| Medium| `backend/domain/scenarios/` | `02-class` | `TC-17` | Phase 07 | **PLANNED** |
| **FR-018** | FAULT_INJECTED event auditing | High | `backend/models/event.py` | `03-sequence` | `TC-18` | Phase 07 | **PLANNED** |
| **FR-019** | IncidentRecord creation upon anomaly detection | High | `backend/domain/anomaly.py` | `04-activity` | `TC-19` | Phase 08 | **PLANNED** |
| **FR-020** | Evidence Proof Matrix hypothesis evaluation | High | `backend/domain/anomaly.py` | `03-sequence` | `TC-20` | Phase 08 | **PLANNED** |
| **FR-021** | Calibrated confidence score calculation | High | `backend/domain/anomaly.py` | `04-activity` | `TC-21` | Phase 08 | **PLANNED** |
| **FR-022** | Virtual ground station network registry | High | `backend/domain/ground.py` | `02-class` | `TC-22` | Phase 09 | **PLANNED** |
| **FR-023** | Contact pass window scheduler | High | `backend/domain/ground.py` | `02-class` | `TC-23` | Phase 09 | **PLANNED** |
| **FR-024** | RF link budget and Doppler shift calculation | Medium| `backend/domain/ground.py` | `02-class` | `TC-24` | Phase 09 | **PLANNED** |
| **FR-025** | Finite state telecommand execution pipeline | High | `backend/domain/commands/` | `03-sequence` | `TC-25` | Phase 10 | **PLANNED** |
| **FR-026** | Flight safety precondition gate enforcement | High | `backend/domain/commands/` | `03-sequence` | `TC-25` | Phase 10 | **PLANNED** |
| **FR-027** | Commanded spacecraft state delta modification| High | `backend/domain/commands/` | `03-sequence` | `TC-25` | Phase 10 | **PLANNED** |
| **FR-028** | Append-only chronological mission event log | High | `backend/models/event.py` | `02-class` | `TC-18` | Phase 11 | **PLANNED** |
| **FR-029** | Mission Time Machine historical playback | High | `backend/domain/replay.py` | `01-use-case` | `TC-05` | Phase 11 | **PLANNED** |
| **FR-030** | Visual REPLAY MODE ACTIVE warning banner | High | `frontend/components/Replay/` | `01-use-case` | `TC-11` | Phase 11 | **PLANNED** |
| **FR-031** | Fleet operational analytics computation | Medium| `backend/domain/analytics.py`| `01-use-case` | `TC-09` | Phase 12 | **PLANNED** |
| **FR-032** | Downloadable incident debrief report generator| High | `backend/domain/reports.py` | `01-use-case` | `TC-19` | Phase 12 | **PLANNED** |
| **FR-033** | What-If recovery simulation sandbox | Medium| `backend/domain/sandbox.py` | `01-use-case` | `TC-20` | Phase 13 | **PLANNED** |
| **FR-034** | Dynamic application configuration API | Low | `backend/core/config.py` | `02-class` | `TC-03` | Phase 02 | **PLANNED** |
| **FR-035** | Role-based authorization enforcement | High | `backend/api/deps.py` | `01-use-case` | `TC-25` | Phase 04 | **PLANNED** |
| **FR-036** | SQLite database compaction & telemetry prune | Low | `backend/models/prune.py` | `02-class` | `TC-09` | Phase 02 | **PLANNED** |

---

## 2. Traceability Summary

- **Total Functional Requirements:** 36
- **Total Mapped Test Cases:** 25
- **Requirements Implemented in Phase 00:** Foundation infrastructure (Health check, monorepo, strict typing)
- **Requirements Implemented in Phase 02:** `FR-001` (Multi-satellite registry), `FR-002` (Operational mode tracking), `FR-003` (Spacecraft physical constants), `FR-009` (Telemetry persistence & queries)
- **Requirements Targeted for Phase 03:** `FR-004`, `FR-005`, `FR-006`, `FR-007`, `FR-012`
- **Requirements Targeted for Phase 04–15:** `FR-008`, `FR-010` through `FR-036`
- **Status Accounting:** 100% of functional requirements have defined component ownership, UML associations, and planned test IDs. Phase 02 test verification suite (`tests/test_traceability_cases.py`) verifies TC-01, TC-02, TC-03, and TC-09 with 100% pass rate.
