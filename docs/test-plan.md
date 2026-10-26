# OrbitOps — Master Test Plan & Quality Assurance Strategy

**Target Alignment:** Software Engineering IA3
**Status:** Phase 01 Baseline Specification

---

## 1. Testing Strategy & Methodology

OrbitOps applies a multi-tier testing pyramid to guarantee deterministic digital twin physics, reliable event persistence, safety-critical command gating, and robust presentation.

```
                  / \
                 / E2E \                Playwright Cross-Browser UI Tests (Phase 14)
                /-------\
               / Integr. \              FastAPI + SQLite WAL Integration Tests
              /-----------\
             / Domain Unit \            Deterministic Subsystem Math & Physics Tests
            /---------------\
           / Static Analysis \          Ruff (Python), ESLint, Strict TypeScript Compiler
          +-------------------+
```

### 1.1 Testing Layers
1. **Domain Unit Tests (`pytest`):** Pure in-memory unit tests of physics calculations (power balance, thermal radiation, ADCS rates, Keplerian propagation) with zero external I/O.
2. **State Machine Verification:** Direct assertion of valid vs. invalid operational mode transitions and command pipelines.
3. **API & Contract Tests (`pytest` + `httpx`):** Verification of REST status codes, Pydantic schemas, and WebSocket frame structures.
4. **Deterministic Scenario Tests:** Running the 4 emergency scenarios with fixed seeds and asserting expected symptom chronologies.
5. **Persistence & WAL Concurrency Tests:** Verifying multi-threaded write throughput without SQLite database lock errors.
6. **Replay Non-Interference Tests:** Verifying that reading historical telemetry or scrubbing the time machine never mutates the active running simulation state.
7. **Frontend Unit & Component Tests:** Verifying UI rendering, health status indicators, and warning banners.

---

## 2. Planned Test Cases (Baseline Catalog)

> [!NOTE]
> All test cases below represent the planned verification matrix for Phases 02–14. In accordance with engineering integrity invariants, tests not yet implemented are explicitly marked with `Actual Result: NOT EXECUTED` and `Status: NOT RUN`.

| Test ID | Req ID | Objective | Preconditions | Inputs / Procedure | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|---|
| **TC-01** | `FR-001` | Verify satellite registry initializes 3 distinct virtual satellites | Fresh DB / Registry startup | Query `SatelliteRegistry.get_all()` | Returns exactly Alpha, Beta, Gamma with valid NORAD IDs | NOT EXECUTED | NOT RUN |
| **TC-02** | `FR-002` | Validate initial satellite operational mode | Satellite instantiated | Inspect `satellite.operational_mode` | Mode equals `INITIALIZING` or `NOMINAL` | NOT EXECUTED | NOT RUN |
| **TC-03** | `FR-003` | Verify physical constants configuration override | Custom `config.py` | Load custom battery capacity ($500\ \text{Wh}$) | Spacecraft calculations use $500\ \text{Wh}$ | NOT EXECUTED | NOT RUN |
| **TC-04** | `FR-004` | Confirm discrete simulation tick advances state | Simulation running | Execute `engine.advance_tick(1.0)` | Sim clock advances by $1.0\ \text{s}$; coordinates update | NOT EXECUTED | NOT RUN |
| **TC-05** | `FR-005` | Test clock pause, resume, and step controls | Engine active | Call `clock.pause()`, `step()`, `resume()` | Clock halts on pause, advances $1\ \text{tick}$ on step | NOT EXECUTED | NOT RUN |
| **TC-06** | `FR-006` | Test cylindrical eclipse entry and solar drop | Spacecraft enters shadow | Propagate orbit into Earth shadow | `is_in_eclipse=True`, `PWR_SOLAR_W` drops to $0.0\ \text{W}$ | NOT EXECUTED | NOT RUN |
| **TC-07** | `FR-007` | Verify coupled power-battery discharge in eclipse | Orbit in eclipse, load $=120\ \text{W}$ | Advance 60 simulation ticks | Battery SOC decreases deterministically ($\Delta \text{SOC} < 0$) | NOT EXECUTED | NOT RUN |
| **TC-08** | `FR-008` | Test telemetry WebSocket broadcast envelope | Client connected | Receive broadcast frame | Frame matches JSON schema with valid sequence ID | NOT EXECUTED | NOT RUN |
| **TC-09** | `FR-009` | Test telemetry sample persistence in SQLite WAL | Active telemetry stream | Write 100 samples to DB | All 100 records retrievable by `(sat_id, sim_time)` | NOT EXECUTED | NOT RUN |
| **TC-10** | `FR-010` | Detect multi-tier telemetry threshold breach | Telemetry within warning bounds | Inject $V_{\text{bus}} = 23.8\ \text{V}$ | Parameter status transitions from `NOMINAL` to `WARNING` | NOT EXECUTED | NOT RUN |
| **TC-11** | `FR-011` | Verify dashboard UI updates on telemetry warning | Frontend connected | Stream warning telemetry frame | Subsystem indicator turns Amber/Red within $1.0\ \text{s}$ | NOT EXECUTED | NOT RUN |
| **TC-12** | `FR-012` | Trigger autonomous safe-mode on critical low SOC | Satellite in nominal mode | Force $\text{SOC} < 20\%$ for $120\ \text{s}$ | Satellite mode transitions to `SAFE_MODE`; payload $=0\ \text{W}$ | NOT EXECUTED | NOT RUN |
| **TC-13** | `FR-013` | Verify 3D Earth globe renders terminator line | WebGL enabled browser | Load Orbital Viewer route | Day/night boundary matches calculated solar subpoint | NOT EXECUTED | NOT RUN |
| **TC-14** | `FR-014` | Confirm orbit trajectory matches Keplerian ground track | Orbit propagator active | Project 1 orbital period | Ground track closes smoothly with proper nodal precession | NOT EXECUTED | NOT RUN |
| **TC-15** | `FR-015` | Validate ground station visibility cone geometry | Satellite approaching Kourou | Compute elevation angle | Elevation angle crosses $10.0^\circ$ at calculated AOS time | NOT EXECUTED | NOT RUN |
| **TC-16** | `FR-016` | Execute SCN-01 (Solar Eclipse Power Crisis) | Alpha in nominal sunlight | Trigger `SCN-01` | Array drive stalls; battery drains; warning triggers | NOT EXECUTED | NOT RUN |
| **TC-17** | `FR-017` | Test scheduled scenario MET conditional trigger | Scenario queued at MET 300 | Run engine until MET $=300$ | Scenario activates precisely at $T = 300\ \text{s}$ | NOT EXECUTED | NOT RUN |
| **TC-18** | `FR-018` | Audit append-only mission event recording | Event emitted | Call `event_store.record()` | Monotonic sequence number increments; record immutable | NOT EXECUTED | NOT RUN |
| **TC-19** | `FR-019` | Instantiate IncidentRecord upon critical alarm | Battery voltage critical | Trigger voltage sag | Incident appears in DB with telemetry snapshot | NOT EXECUTED | NOT RUN |
| **TC-20** | `FR-020` | Assemble Evidence Proof Matrix for anomaly | Incident active | Query `investigator.evaluate()` | Proof matrix returns supporting vs. refuting proofs | NOT EXECUTED | NOT RUN |
| **TC-21** | `FR-021` | Verify calibrated confidence score behavior | Partial telemetry available | Run diagnosis on incomplete data | Confidence score evaluates to $< 70\%$ | NOT EXECUTED | NOT RUN |
| **TC-22** | `FR-022` | Compute Doppler frequency curve during ground pass | Beta passes Madrid | Sample carrier frequency across pass | Doppler curve shifts from positive to negative at zenith | NOT EXECUTED | NOT RUN |
| **TC-23** | `FR-023` | Reject command when satellite is out of contact | Satellite out of contact pass | Submit `CMD_SHED_PAYLOAD` | Command rejected: `ERR_OUT_OF_CONTACT_WINDOW` | NOT EXECUTED | NOT RUN |
| **TC-24** | `FR-024` | Execute validated command during active contact | Satellite in active pass ($\text{El} > 15^\circ$) | Submit valid command | Status advances to `APPROVED` $\to$ `COMPLETED`; load sheds | NOT EXECUTED | NOT RUN |
| **TC-25** | `FR-025` | Verify Mission Time Machine replay isolation | Replay active, seeking $T-10\text{m}$ | Inspect active simulation state | Active simulation state and clock are unaffected | NOT EXECUTED | NOT RUN |

---

## 3. Scenario Acceptance Criteria

1. **SCN-01 (Solar Eclipse Power Crisis):**
   - *Pass:* Battery SOC drains upon eclipse entry; solar generation fails to resume upon exit; emergency alert is generated; shedding payload stabilizes SOC above $35\%$.
   - *Fail:* Battery does not drain, or simulation crashes on mode transition.
2. **SCN-02 (Communication Blackout):**
   - *Pass:* RF lock drops to FALSE; telemetry drops; command validation rejects uplinks; switching to B-side transponder recovers carrier lock with $\text{SNR} \ge 12\ \text{dB}$.
   - *Fail:* Commands succeed despite carrier loss, or transponder state fails to switch.
3. **SCN-03 (Thermal Runaway Emergency):**
   - *Pass:* Radiator failure causes amplifier temperature to climb past $+65^\circ\text{C}$; thermal alert triggers; commanding amplifier power-down stops temperature rise below $+75^\circ\text{C}$.
   - *Fail:* Temperature climbs past $+75^\circ\text{C}$ without burnout protection.
4. **SCN-04 (Conflicting Sensor Readings):**
   - *Pass:* Horizon sensor reports rapid roll rate error while 3-axis gyros report $0.0^\circ/\text{s}$; investigator proof matrix highlights sensor conflict; operator isolates bad sensor to maintain pointing.
   - *Fail:* System treats sensor noise as genuine tumble and fires thrusters uncontrollably.
