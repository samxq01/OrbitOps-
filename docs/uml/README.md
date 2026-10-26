# OrbitOps — UML Architectural Diagrams Baseline

This directory contains the five standards-based UML design diagrams for **OrbitOps**, modeling user interactions, object structures, dynamic telecommand interactions, fault resolution workflows, and spacecraft operational state machines.

---

## 1. Diagram Catalog

| File | Diagram Type | Core Entities & Scope |
|---|---|---|
| [01-use-case.puml](file:///e:/Sem%203/SE/mp/OrbitOps/docs/uml/01-use-case.puml) | **Use Case Diagram** | Actors (`Mission Operator`, `Mission Administrator`, `Observer`), system boundaries, fleet monitoring, telecommands, incident diagnosis, fault injection, and replay. |
| [02-class.puml](file:///e:/Sem%203/SE/mp/OrbitOps/docs/uml/02-class.puml) | **Domain Class Diagram** | Domain models: `Mission`, `Satellite`, `SatelliteSubsystem` (Power, Thermal, ADCS, Comms, Payload), `TelemetrySample`, `FaultScenario`, `Incident`, `EvidenceRecord`, `GroundStation`, `ContactWindow`, `SatelliteCommand`, `CommandValidator`, and `MissionEvent`. |
| [03-sequence.puml](file:///e:/Sem%203/SE/mp/OrbitOps/docs/uml/03-sequence.puml) | **Sequence Diagram** | Dynamic lifecycle of anomaly diagnosis and precondition-validated telecommand recovery (`Mission Operator` $\to$ `Frontend` $\to$ `FastAPI` $\to$ `Mission Service` $\to$ `Anomaly Investigator` $\to$ `Command Validator` $\to$ `Simulation Engine` $\to$ `Event Repository`). |
| [04-activity.puml](file:///e:/Sem%203/SE/mp/OrbitOps/docs/uml/04-activity.puml) | **Activity Diagram** | End-to-end anomaly detection and recovery decision pipeline, including telemetry validation, incident instantiation, evidence ranking, precondition verification, and recovery outcome validation. |
| [05-state-machine.puml](file:///e:/Sem%203/SE/mp/OrbitOps/docs/uml/05-state-machine.puml) | **State Machine Diagram** | Satellite operational modes: `INITIALIZING`, `NOMINAL`, `DEGRADED`, `SAFE_MODE`, `EMERGENCY`, `RECOVERY`, and `OFFLINE` with explicit transition guards, actions, and rejection of illegal direct transitions. |

---

## 2. Rendering PlantUML Diagrams

All files are written in standard PlantUML specification format. They can be viewed or rendered locally or online using several standard methods:

### Method A: VS Code Extension (Recommended for Development)
1. Install the **PlantUML** extension (`jebbs.plantuml`) in VS Code.
2. Ensure Java 17+ is installed (or use the built-in online server renderer).
3. Open any `.puml` file and press `Alt + D` to render an interactive preview.

### Method B: PlantUML Command Line (CLI)
If `plantuml.jar` is downloaded:
```bash
# Render all diagrams to PNG
java -jar plantuml.jar docs/uml/*.puml

# Render all diagrams to SVG
java -jar plantuml.jar -tsvg docs/uml/*.puml
```

### Method C: Web-Based Viewer (Zero Local Setup)
Copy and paste the raw contents of any `.puml` file into:
- [PlantText Online Editor](https://www.planttext.com/)
- [PlantUML Official Server](https://www.plantuml.com/plantuml/uml/)

---

## 3. Diagram Consistency & Architecture Invariants

1. **Class Naming Alignment:** Class and enumeration names in `02-class.puml` directly correspond to planned Python domain models in `backend/app/domain/` and schemas in `backend/app/schemas/`.
2. **State Separation:** `05-state-machine.puml` models the spacecraft operational state machine (`SatelliteMode`), which is kept strictly decoupled from `CommandStatus` (`QUEUED` $\dots$ `COMPLETED`) and `IncidentSeverity` (`INFO` $\dots$ `CRITICAL`).
3. **Evidence Rigor:** Both `03-sequence.puml` and `04-activity.puml` illustrate the evidence assembly pipeline where candidate hypotheses require supporting vs. counter-evidence proofs before operator recommendation.
