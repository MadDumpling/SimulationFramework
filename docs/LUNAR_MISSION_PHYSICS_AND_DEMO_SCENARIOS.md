# Lunar Mission Analysis: Physics, Mission Logic, and Example Scenarios

This guide explains how the Spacecraft Configurator evaluates a lunar mission, what the reported metrics mean, and how to demonstrate successful and unsuccessful mission outcomes.

The platform combines spacecraft design, engineering screening, trajectory analysis, and Earth-Moon mission evaluation into a single workflow. Users can assemble a spacecraft, evaluate its engineering characteristics, and determine whether the design satisfies the requirements of a modeled lunar mission.

> **Important:** Mission results should be interpreted as engineering-screening and mission-feasibility assessments rather than flight certification. Vehicle components use representative engineering models unless otherwise stated. A successful result indicates that the modeled trajectory reaches the Moon's sphere of influence under the assumptions described in this document. It does not establish launch readiness, lunar capture, orbit insertion, or safe landing capability.

---

# What Uses Real-World Data?

The mission environment incorporates real-world aerospace and astronomy data:

- Historical Apollo mission references
- Apollo 11 launch-site reference data (LC-39A)
- JPL DE440s ephemerides
- Date-specific Earth-Moon geometry
- Date-specific Moon and Sun positions
- Lambert transfer calculations
- Numerical trajectory propagation

Mission geometry changes with departure date and transfer duration.

# What Uses Representative Engineering Models?

The vehicle-design system uses simplified engineering models so users can quickly explore design tradeoffs.

Examples include:

- Propulsion-system abstractions
- Power-system ratings
- RCS subsystem ratings
- Landing-gear representations
- Simplified mass and performance models

These models are intended to help users understand engineering relationships rather than reproduce flight-certified hardware.

---

# Run a Showcase Scenario

1. Start the application:

```bash
python app.py
```

2. Open the **Mission** tab.
3. Select a **Demo scenario**.
4. Click **Load Demo Scenario**.
5. Click **Run Lunar Mission Simulation**.
6. Review the mission verdict and detailed mission report.

Loading a scenario automatically configures a spacecraft preset together with reference mission inputs.

All built-in scenarios use **2026-10-30** to ensure repeatable demonstrations. Because the simulation uses date-specific ephemerides, mission geometry can change when departure dates or transfer durations change.

The reference encounter scenarios demonstrate modeled lunar encounters under the assumptions of the current mission model. They should not be interpreted as evidence of launch readiness, operational success, or landing capability.

---

# What the Simulator Calculates

## 1. Vehicle Mass

Vehicle wet mass is calculated as:

```text
wet mass = total dry mass + total loaded propellant mass
```

Only propellant compatible with the installed engine contributes to propulsion calculations.

Important implications:

- Compatible propellant contributes to delta-v.
- Incompatible propellant still contributes mass.
- Residual propellant contributes mass but is not considered usable.

A vehicle can therefore become heavier without becoming more capable.

---

## Installed Spacecraft Subsystems

In addition to engines and tanks, the configurator supports:

### Landing Legs

Configurable values include:

- Leg count
- Leg length
- Footprint radius
- Footpad radius
- Rated load

Landing-leg geometry contributes to visualization and stability screening.

The simulator does not currently model:

- Structural failure
- Contact forces
- Terrain interaction
- Landing dynamics

### RCS Thrusters

Configurable values include:

- Thrust
- Specific impulse
- Thruster count
- Electrical load

RCS systems are displayed and analyzed separately from the main propulsion system.

The current mission model does not:

- Consume RCS propellant
- Perform attitude control
- Use RCS thrust during trajectory propagation

### Solar Panels

Configurable values include:

- Deployed area
- Rated electrical generation

### Batteries

Configurable values include:

- Energy capacity
- Maximum charge power
- Maximum discharge power

### Avionics

Configurable values include:

- Electrical load
- Redundancy

The power summary reports installed generation, load, storage, and charge/discharge capability.

The mission model does not currently simulate:

- Solar illumination
- Pointing constraints
- State of charge
- Power usage over time

---

## Assembly and Placement

The placement system supports:

- Automatic layout
- Free XYZ positioning
- Parent-child attachments
- Local rotations
- Mirror copies

The editor is intended as a visualization and assembly tool.

The system does not currently validate:

- Structural loads
- Mechanical clearances
- Wiring
- Deployments
- Collision avoidance

---

## 2. Thrust-to-Weight Ratio (TWR)

TWR is calculated as:

```text
TWR = total thrust / (wet mass × g₀)

g₀ = 9.80665 m/s²
```

Interpretation:

- **TWR < 1** → insufficient thrust to lift off.
- **TWR = 1** → thrust balances weight.
- **TWR > 1** → thrust exceeds weight.

This is a screening calculation rather than a launch simulation.

The model does not simulate:

- Atmospheric drag
- Gravity losses
- Steering losses
- Launch dynamics

---

## 3. Delta-v

Mass flow is estimated using:

```text
mass flow = thrust / (Isp × g₀)

ideal burn time = usable propellant / mass flow
```

Delta-v is estimated using the Tsiolkovsky rocket equation:

```text
Δv = Isp × g₀ × ln(wet mass / final mass)

final mass = wet mass − usable propellant
```

Where:

- Higher Isp improves efficiency.
- More propellant increases potential delta-v.
- Additional mass reduces returns.

This is an idealized calculation.

It does not account for:

- Atmospheric losses
- Gravity losses
- Maneuver margins
- Reserves

---

## 4. Earth-Ascent and TLI Screening

The model reserves:

```text
9.4 km/s
```

for Earth ascent.

This represents an approximate Earth-to-orbit allowance rather than a simulated launch.

Remaining mission budget:

```text
remaining delta-v = total delta-v − 9.4 km/s
```

The analysis first checks:

1. Positive thrust
2. TWR > 1
3. Sufficient ascent delta-v

If those conditions pass, the mission solver calculates a date-specific translunar injection requirement.

A design may therefore:

- Pass launch screening
- Pass ascent screening
- Still fail the lunar mission

if insufficient delta-v remains for the required transfer.

---

## 5. Earth-to-Moon Transfer Evaluation

For a selected departure date and transfer duration:

1. A Lambert solver determines the transfer velocity needed to reach the Moon's future position.
2. Required TLI delta-v is calculated.
3. If the vehicle can supply that delta-v, trajectory propagation begins.

Trajectory propagation includes:

- Earth gravity
- Moon gravity
- Sun gravity

Moon and Sun positions are obtained from:

```text
JPL DE440s
```

ephemeris data.

Trajectory integration uses SciPy's DOP853 integrator.

Default settings:

```text
Maximum integration step = 300 seconds
Evaluation samples = 5000
```

These are numerical integration settings and not physical measurements.

---

## 6. What “Reached the Moon” Means

The simulator estimates the Moon's sphere of influence (SOI):

```text
SOI radius =
mean Earth-Moon distance × (Moon GM / Earth GM)^(2/5)
```

If the propagated trajectory enters that region:

```text
Lunar Arrival = TRUE
```

The report also calculates:

```text
SOI margin

surface clearance
```

Interpretation:

- Positive SOI margin → entered lunar SOI.
- Negative SOI margin → missed lunar SOI.
- Negative surface clearance → modeled surface intersection.

A lunar arrival means:

✅ A successful lunar-arrival screening outcome.

It does **not** mean:

❌ Lunar orbit insertion

❌ Lunar capture

❌ Controlled descent

❌ Landing

❌ Operational mission success

---

# Showcase Scenarios

| Scenario | Purpose |
|-----------|----------|
| Lunar encounter — no surface impact | Successful lunar-arrival screening |
| Lunar encounter — surface impact estimate | Demonstrates encounter geometry changes |
| Failure — insufficient lift-off thrust | Demonstrates TWR failure |
| Failure — insufficient Earth-ascent delta-v | Demonstrates ascent-budget failure |
| Failure — insufficient TLI propellant | Demonstrates transfer-budget failure |
| Failure — engine/tank propellant mismatch | Demonstrates compatibility constraints |

These scenarios are designed to illustrate engineering tradeoffs and mission constraints.

---

# Apollo 11 Historical Reference

The Mission tab includes a source-backed Apollo 11 reference profile derived from NASA documentation.

The reference includes:

- Launch date
- Launch site
- Mission timeline
- Parking-orbit state data
- Translunar injection reference values

This reference provides historical context and aerospace provenance.

It is intentionally separate from the currently edited spacecraft.

It should not be interpreted as a Saturn V simulation.

---

# Design Tradeoffs

The configurator helps visualize common spacecraft-design tradeoffs:

### More Propellant

Pros:

- Increased delta-v

Cons:

- Increased mass
- Lower TWR

### More Thrust

Pros:

- Higher TWR
- Better launch margin

Cons:

- Does not automatically improve mission delta-v

### Larger Tanks

Pros:

- Potentially more propellant

Cons:

- Added mass

Additional tank capacity only helps when compatible propellant is loaded.

### Propellant Compatibility

Compatible engine and tank propellants are required for fuel to count as usable.

### Mission Success

Passing launch and delta-v checks does not guarantee lunar arrival.

Trajectory geometry still matters.

---

# Model Scope

The current mission model evaluates:

✅ Vehicle mass properties

✅ Delta-v

✅ Thrust-to-weight ratio

✅ Propellant compatibility

✅ Electrical-power balance

✅ Mission-screening requirements

✅ Translunar injection requirements

✅ Date-specific Earth-Moon geometry

✅ Numerical trajectory propagation

✅ Lunar sphere-of-influence arrival

The current model does **not** evaluate:

❌ Atmospheric launch dynamics

❌ Earth rotation effects

❌ Staging

❌ Finite-duration burns

❌ Mid-course corrections

❌ Lunar orbit insertion

❌ Powered descent

❌ Terrain interaction

❌ Touchdown dynamics

❌ Failure probability analysis

❌ Navigation uncertainty

---

# Interpreting Results

A positive mission result should be interpreted as a successful lunar-arrival screening outcome within the assumptions of the current model.

Additional analysis would be required to establish:

- Launch readiness
- Vehicle certification
- Orbital operations
- Lunar capture
- Landing performance
- Operational mission success

The viewport animation illustrates the mission verdict for presentation purposes and is not the numerically propagated trajectory.
