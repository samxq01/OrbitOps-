# OrbitOps — Satellite Digital Twin Simulation Specification

**Target Implementation:** Phase 03 (Deterministic Satellite Digital Twin Engine)
**Document Identifier:** `ORBITOPS-SIM-SPEC-V1.0`
**Classification:** Educational Simplified Spacecraft Physics Engine

---

## 1. Simulation Philosophy & Fidelity Boundaries

> [!IMPORTANT]
> **Fidelity Statement & Educational Boundary:**
> OrbitOps implements a **simplified, deterministic, coupled lumped-parameter simulation model**. It is designed for educational operations training and software engineering evaluation, NOT high-fidelity orbital mechanics or thermal-vacuum qualification. All physical equations use documented first-order approximations.

---

## 2. Power Subsystem Mathematical Model

The power subsystem models energy generation from photovoltaic arrays, unregulated bus distribution, battery electrochemical storage, and subsystem electrical loads.

```
+-------------------+           +-------------------+
| Solar Photovoltaic| --------> | Unregulated Power | --------> [ Subsystem Loads: ADCS, ]
| Arrays (P_solar)  |           | Bus (V_bus)       |           [ Comms, Payloads, Heat  ]
+-------------------+           +---------+---------+
                                          |
                                          v (Charge / Discharge)
                                +-------------------+
                                | Battery Storage   |
                                | (SOC %, E_batt)   |
                                +-------------------+
```

### 2.1 Equations of State

1. **Solar Array Electrical Generation ($P_{\text{solar}}$):**
   $$P_{\text{solar}}(t) = G_{\text{solar}} \cdot A_{\text{array}} \cdot \eta_{\text{cell}} \cdot \cos(\theta_{\text{sun}}) \cdot (1 - \delta_{\text{eclipse}})$$
   - $G_{\text{solar}} = 1361.0\ \text{W/m}^2$ (Solar Constant at 1 AU).
   - $A_{\text{array}}$: Effective solar array area ($1.2\ \text{m}^2$ for Alpha, $1.8\ \text{m}^2$ for Beta, $0.8\ \text{m}^2$ for Gamma).
   - $\eta_{\text{cell}} = 0.28$ ($28\%$ multi-junction GaInP/GaAs efficiency).
   - $\theta_{\text{sun}}$: Sun incidence angle relative to array surface normal ($0^\circ$ nominal in sun-tracking).
   - $\delta_{\text{eclipse}} \in \{0, 1\}$: Binary eclipse indicator ($1$ if line-of-sight to sun is occluded by Earth).

2. **Total Spacecraft Electrical Load ($P_{\text{load}}$):**
   $$P_{\text{load}}(t) = P_{\text{bus\_base}} + P_{\text{adcs}} + P_{\text{comms}} + P_{\text{payload}} + P_{\text{heaters}}$$
   - Nominal base avionics: $P_{\text{bus\_base}} = 25.0\ \text{W}$.
   - ADCS reaction wheels: $P_{\text{adcs}} = 15.0\ \text{W}$ nominal, $35.0\ \text{W}$ during slew.
   - Communications: $P_{\text{comms}} = 20.0\ \text{W}$ standby, $80.0\ \text{W}$ active downlink transmit.
   - Payload: $P_{\text{payload}} = 180.0\ \text{W}$ (Alpha imager), $120.0\ \text{W}$ (Beta relay), $35.0\ \text{W}$ (Gamma probe).
   - Heaters: $P_{\text{heaters}} = 40.0\ \text{W}$ when active.

3. **Net Battery Power ($P_{\text{batt}}$) & Storage Dynamics:**
   $$P_{\text{batt}}(t) = P_{\text{solar}}(t) - P_{\text{load}}(t)$$
   If $P_{\text{batt}} > 0$: Battery is **Charging** (efficiency $\eta_{\text{charge}} = 0.92$).
   If $P_{\text{batt}} < 0$: Battery is **Discharging** (efficiency $\eta_{\text{discharge}} = 0.96$).

   $$\frac{dE_{\text{batt}}}{dt} = \begin{cases} P_{\text{batt}} \cdot \eta_{\text{charge}}, & P_{\text{batt}} \ge 0 \\ \frac{P_{\text{batt}}}{\eta_{\text{discharge}}}, & P_{\text{batt}} < 0 \end{cases}$$

4. **State of Charge ($\text{SOC}$):**
   $$\text{SOC}(t) = \left( \frac{E_{\text{batt}}(t)}{E_{\text{capacity}}} \right) \times 100\%$$
   - Clamped to $[0.0\%, 100.0\%]$.
   - $E_{\text{capacity}}$: $320\ \text{Wh}$ (Alpha), $480\ \text{Wh}$ (Beta), $220\ \text{Wh}$ (Gamma).

5. **Bus Voltage Characteristic ($V_{\text{bus}}$):**
   $$V_{\text{bus}}(t) = V_{\text{nominal}} + k_{\text{curve}} \cdot (\text{SOC} - 50) - I_{\text{load}} \cdot R_{\text{internal}}$$
   - Nominal: $V_{\text{nominal}} = 28.0\ \text{V}$, $R_{\text{internal}} = 0.08\ \Omega$.
   - Operational voltage range: $22.0\ \text{V}$ (depleted) to $30.5\ \text{V}$ (fully charged).

---

## 3. Thermal Subsystem Mathematical Model

Thermal dissipation is modeled via a lumped-capacitance nodal energy balance combining internal electrical dissipation and Stefan-Boltzmann radiative exchange with deep space.

### 3.1 Equations of State

1. **Space Radiative Equilibrium:**
   $$m \cdot c_p \cdot \frac{dT}{dt} = \dot{Q}_{\text{in}} - \dot{Q}_{\text{out}}$$
   - $\dot{Q}_{\text{in}} = P_{\text{dissipated}} + \alpha_{\text{solar}} \cdot A_{\text{proj}} \cdot G_{\text{solar}} \cdot (1 - \delta_{\text{eclipse}}) + \dot{Q}_{\text{albedo}}$
   - $\dot{Q}_{\text{out}} = \epsilon \cdot \sigma \cdot A_{\text{radiator}} \cdot (T^4 - T_{\text{space}}^4)$
   - $T_{\text{space}} = 3.0\ \text{K}$ (Deep space background).
   - $\sigma = 5.67037 \times 10^{-8}\ \text{W/(m}^2\text{K}^4)$ (Stefan-Boltzmann constant).
   - $\epsilon = 0.85$ (Radiator infrared emissivity).
   - $\alpha_{\text{solar}} = 0.15$ (White thermal paint solar absorptivity).
   - $m \cdot c_p$: Lumped thermal heat capacity ($\approx 45000\ \text{J/K}$ for spacecraft bus).

2. **Thermostatic Heater Control Loop:**
   - If $T_{\text{bus}} < +5.0^\circ\text{C}$: Thermostat turns survival heaters **ON** ($+40\ \text{W}$).
   - If $T_{\text{bus}} > +15.0^\circ\text{C}$: Thermostat turns survival heaters **OFF**.

3. **Thermal Threshold Matrix:**
   - Nominal Range: $+5.0^\circ\text{C}$ to $+35.0^\circ\text{C}$.
   - Warning Range: $-5.0^\circ\text{C}$ to $+5.0^\circ\text{C}$ or $+35.0^\circ\text{C}$ to $+50.0^\circ\text{C}$.
   - Critical Range: $< -15.0^\circ\text{C}$ or $> +65.0^\circ\text{C}$.

---

## 4. Attitude Determination & Control (ADCS)

The ADCS model simulates closed-loop spacecraft orientation without solving full flexible-body tensor mechanics.

1. **Pointing Modes:**
   - `NADIR_POINTING`: Payload points toward center of Earth ($z$-axis toward nadir). Nominal for optical imaging.
   - `SUN_POINTING`: Solar arrays oriented perpendicular to the solar vector. Maximizes power generation during charging or recovery.
   - `SAFE_TUMBLE`: Uncontrolled slow rotation ($> 5^\circ/\text{s}$) induced by fault or actuator failure.
2. **Angular Rate Dynamics:**
   $$\vec{\omega}(t + \Delta t) = \vec{\omega}(t) + \frac{\vec{\tau}_{\text{control}} + \vec{\tau}_{\text{disturbance}}}{I_{\text{sat}}} \cdot \Delta t$$
   - Control torque from reaction wheels: limited to $\tau_{\text{max}} = 0.05\ \text{N}\cdot\text{m}$.
   - Disturbance torque (gravity gradient & atmospheric drag): modeled as low-amplitude Gaussian white noise ($\sigma = 10^{-4}\ \text{N}\cdot\text{m}$).
   - Nominal angular rate: $|\vec{\omega}| < 0.05^\circ/\text{s}$.

---

## 5. Communications & Ground Link Budget

1. **Carrier Lock & Line-of-Sight Window:**
   - Contact window is active when ground station elevation angle $\theta_{\text{el}} \ge 10.0^\circ$.
2. **Signal-to-Noise Ratio ($E_b/N_0$):**
   $$\text{SNR}_{\text{dB}} = P_{\text{tx\_dBW}} + G_{\text{tx\_dBi}} + G_{\text{rx\_dBi}} - \text{FSPL}_{\text{dB}} - 10\log_{10}(k \cdot T_{\text{sys}} \cdot R_{\text{data}})$$
   - Free Space Path Loss:
     $$\text{FSPL}_{\text{dB}} = 20\log_{10}(d) + 20\log_{10}(f) + 92.45$$
     where $d$ is distance in km and $f$ is frequency in GHz ($2.2\ \text{GHz}$ S-band).
   - Nominal SNR during pass: $12.0\dots 18.0\ \text{dB}$.
   - Loss of Signal threshold: $\text{SNR} < 3.0\ \text{dB}$.
3. **Doppler Frequency Shift ($\Delta f$):**
   $$\Delta f(t) = - \frac{v_{\text{rel}}(t)}{c} \cdot f_0$$
   - $v_{\text{rel}}$: Relative line-of-sight velocity between satellite and ground antenna.
   - S-band Doppler swing: approx $\pm 45\ \text{kHz}$ for LEO at $7.5\ \text{km/s}$.

---

## 6. Orbital Mechanics & Eclipse Determination

1. **Simplified Two-Body Orbit Propagation:**
   Mean orbital motion ($n$):
   $$n = \sqrt{\frac{\mu}{a^3}}$$
   - $\mu = 398600.4418\ \text{km}^3/\text{s}^2$ (Earth gravitational parameter).
   - True anomaly advances as: $\nu(t + \Delta t) = \nu(t) + n \cdot \Delta t$.
2. **Cylindrical Earth Shadow Model:**
   A satellite at position vector $\vec{r}$ enters eclipse when:
   $$\vec{r} \cdot \hat{s} < 0 \quad \text{and} \quad |\vec{r} - (\vec{r} \cdot \hat{s})\hat{s}| < R_{\text{Earth}}$$
   - $\hat{s}$: Unit vector pointing toward the Sun.
   - $R_{\text{Earth}} = 6371.0\ \text{km}$.
   - Yields approx $35\ \text{minutes}$ eclipse per $95\ \text{minute}$ LEO orbit.

---

## 7. Determinism, Seeded Scenarios & State Checkpointing

1. **Deterministic Seeds:**
   - Every scenario runs with a seeded pseudo-random generator (`seed=42` default) so that sensor noise, atmospheric fluctuations, and trigger offsets repeat identically.
2. **State Checkpointing Format:**
```python
checkpoint = {
    "sim_time": "2026-10-26T14:30:00Z",
    "warp": 1.0,
    "satellites": {
        "SAT-001": {
            "mode": "NOMINAL",
            "coords": {"lat": 14.2, "lon": -45.1, "alt": 550.0},
            "power": {"soc": 91.2, "bus_v": 28.1, "solar_w": 420.0},
            "thermal": {"bus_c": 22.1, "pl_c": 26.0},
            "adcs": {"mode": "NADIR_POINTING", "rate": 0.02},
            "payload": {"status": "STANDBY", "storage_mb": 120.0}
        }
    }
}
```
3. **Replay Isolation:**
   - Replay reads strictly from historical `telemetry_samples` and `mission_events`.
   - The active `SimulationEngine` memory space is completely untouched during playback.

---

## 8. Phase 03 Implementation Architecture & Standalone Verification

### 8.1 Simulation Update Sequence (Per Satellite, Per Tick)

The digital twin advances in a deterministic, documented 19-step update order:
1. **Orbital Propagation:** True anomaly advances via mean motion $\nu(t + \Delta t) = \nu(t) + n\cdot \Delta t$; ECI $(x,y,z)$ coordinates computed; geodetic latitude, longitude, and altitude derived accounting for Earth rotation.
2. **Eclipse Detection:** Cylindrical shadow evaluated using new satellite position and Sun direction vector.
3. **ADCS Sun Incidence:** Effective incidence angle calculated from orbital plane geometry and pointing mode (`SUN_POINTING` drives angle to $0^\circ$).
4. **ADCS Rate Integration:** Control torques and seeded disturbance torques integrated; safe-tumble detected if rate $> 5.0^\circ/\text{s}$.
5. **Payload State Update:** Power consumption evaluated based on operational mode and payload activity.
6. **Communications State Update:** Transmitter power and local link quality estimated based on active/standby state.
7. **Heater State Evaluation:** Thermostatic hysteresis evaluated using prior bus temperature to prevent circularity.
8. **Solar Power Generation:** Generation computed from solar constant, effective cell area, cell efficiency, incidence cosine, and eclipse flag.
9. **Total Electrical Load:** Sum of avionics base, ADCS, comms, payload, and active heater loads.
10. **Battery Energy Integration:** Stored energy integrated using net power and charge ($\eta = 0.92$) / discharge ($\eta = 0.96$) efficiencies; SOC clamped to $[0\%, 100\%]$.
11. **Bus Voltage Calculation:** Unregulated voltage calculated with linear SOC curve and internal resistance voltage drop.
12. **Thermal State Integration:** Lumped radiative exchange with deep space $(3\ \text{K})$ and heat input from electrical dissipation $(60\%)$ and solar absorption.
13. **Subsystem Health Classification:** Power, thermal, ADCS, comms, and payload classified as `NOMINAL`, `WARNING`, or `CRITICAL`.
14. **Autonomous Mode Evaluation:** Sustained low SOC ($< 20\%$ for 60 ticks), high temperature ($> 65^\circ\text{C}$ for 60 ticks), or critical tumble ($> 5.0^\circ/\text{s}$) triggers `SAFE_MODE`.
15. **Safe Mode Recovery Orienting:** ADCS automatically commands `SUN_POINTING` when entering `SAFE_MODE` to maximize battery recovery.
16. **Telemetry Frame Generation:** Monotonically sequenced, typed `TelemetryFrame` generated from authoritative physics state with small deterministic sensor noise.

### 8.2 Standalone Demonstration & Verification

OrbitOps provides an isolated simulation demonstration that runs without database alterations or web server dependencies:

```bash
cd backend
uv run python -m app.simulation.demo
# Or via pyproject script:
uv run orbitops-demo
```

The demonstration verifies:
- Initialization of all three virtual spacecraft (`SAT-001`, `SAT-002`, `SAT-003`).
- Advancing simulation time by 100 logical ticks.
- Dynamic pause and single-step advancing.
- Full snapshot capture and atomic restoration into an independent engine instance.
- Exact floating-point determinism across repeated runs with identical random seed (`seed=42`).
- 1000-tick extended stability (no NaNs, infinite values, or unphysical SOC bounds).
