# Lunar Mission Demo: Physics, Math, and Example Designs

This guide explains what the configurator calculates, what its numbers mean, and
how to run the example success and failure scenarios. It is written for a live
demo: each equation is followed by a plain-language interpretation.

> **Scope:** This application is an educational reachability demonstration, not
> a flight-design tool. “Lunar arrival” means that a simplified propagated path
> enters the Moon's sphere of influence. It does not mean lunar orbit, a
> controlled descent, or a safe landing. Example component values are synthetic
> and deliberately unrealistic.

## Run a showcase scenario

1. Start the app with `python app.py`.
2. Open the **Mission** tab.
3. Choose a **Demo scenario** and select **Load demo scenario**.
4. Select **Run Lunar Mission Simulation**.
5. Read the verdict and the expanded numbers in the Mission tab.

Loading a scenario selects its spacecraft preset and sets the example departure
date and transfer duration. All preset scenarios use **2026-10-30** so their
inputs are consistent with the bundled demonstration settings. The encounter
examples use this fixed date for their reference results; Moon geometry and
closest approach can vary when you change the date or transfer duration, so use
the values in the UI for the run you are presenting.

All values are illustrative. The encounter examples use a fixed reference date
and transfer duration so the demonstration is repeatable. The “successful”
scenario demonstrates a modeled lunar encounter, not successful flight hardware
or a landing.

## What the simulator calculates

### 1. Vehicle mass

The analysis adds the dry mass of every component and the loaded propellant in
every tank:

```text
wet mass = total dry mass + total loaded propellant mass
```

For the engine's performance calculations, only usable propellant in tanks
whose fuel type matches the engine is burnable. Residual propellant is not
usable. An incompatible tank still adds mass, but it does not add burnable
fuel. That is why a full tank can make a design heavier without helping it fly.

### 2. Thrust-to-weight ratio: can it lift off?

```text
TWR = total thrust / (wet mass × g₀)
g₀ = 9.80665 m/s²
```

Weight is the downward force of gravity on the loaded vehicle. TWR compares
engine force with that weight:

- **TWR below 1:** thrust is less than weight; the simplified vehicle cannot
  lift off vertically.
- **TWR equal to 1:** thrust only balances weight; there is no upward
  acceleration in this idealized check.
- **TWR above 1:** thrust exceeds weight in the check. A real launch needs
  additional margin for drag, steering, and gravity losses.

This is a gate, not a launch simulation. The app does not simulate an actual
Earth launch, atmosphere, or gravity losses.

### 3. Ideal rocket-equation delta-v: how much speed could the propellant add?

The engine mass-flow estimate is:

```text
mass flow = thrust / (Isp × g₀)
ideal burn time = usable propellant / mass flow
```

`Isp` (specific impulse) describes how efficiently an engine uses propellant.
Higher Isp means less propellant is needed for a given thrust and burn time.

The ideal single-stage speed-change estimate is the Tsiolkovsky rocket
equation:

```text
Δv = Isp × g₀ × ln(wet mass / final mass)
final mass = wet mass − usable propellant
```

The logarithm matters: adding propellant improves ideal delta-v, but each
additional amount gives a smaller gain. The engine and tank also have to be
carried. This ideal equation does not subtract atmospheric drag, steering
losses, finite-burn gravity losses, or reserves.

### 4. Earth-ascent and trans-lunar injection (TLI) checks

The model reserves **9.4 km/s** as an approximate Earth-surface-to-low-Earth-
orbit ascent allowance. It is a screening assumption, not a simulated ascent.

After that allowance, the approximate remaining budget is:

```text
delta-v remaining for TLI = ideal vehicle delta-v − 9.4 km/s
```

The initial vehicle screen checks that the vehicle has positive thrust, TWR
above 1, and enough ideal delta-v for Earth ascent. For a particular run, the
simulator then calculates a date- and duration-specific TLI requirement. The
remaining vehicle delta-v must cover that exact injection. A design may pass
the initial ascent check and still fail at this later TLI check.

The Analysis tab's approximate lunar pre-screen uses a typical 3.2 km/s TLI
allowance (about **12.6 km/s total**). The Mission tab reports the specific
Lambert TLI value for the selected run.

### 5. From a transfer guess to a modeled lunar encounter

For the selected departure time and transfer duration, a Lambert solver
calculates the ideal starting velocity that connects an assumed point on a
200 km circular Earth parking orbit to the Moon's ephemeris position at the
arrival time. This gives a required TLI delta-v; it is an impulsive burn, not a
modeled engine firing.

If the vehicle has enough delta-v, the program propagates the resulting
position and velocity under simplified Sun, Earth, and Moon gravity. In
plain-language form, each body's pull depends on its gravitational parameter
and distance:

```text
acceleration from one body = gravitational parameter / distance²
```

The integration combines those accelerations over time. The Moon and Sun
terms are expressed relative to Earth, so the model accounts for the
differential pull on the spacecraft versus Earth. It uses JPL DE440s to obtain
the date-specific Moon and Sun positions.

In the model's Earth-centered coordinates, the acceleration is:

```text
r̈ = −μE r / |r|³
     + μM [(rM − r) / |rM − r|³ − rM / |rM|³]
     + μS [(rS − r) / |rS − r|³ − rS / |rS|³]
```

`r` is the spacecraft's position relative to Earth; `rM` and `rS` are the
Moon's and Sun's positions relative to Earth. `μE`, `μM`, and `μS` are their
gravitational parameters (`G × body mass`). The first term is Earth's pull.
Each bracket is the Moon's or Sun's pull on the spacecraft minus its pull on
Earth. The solver integrates this acceleration together with `ṙ = v`.

The integration uses SciPy's DOP853 solver. Its default maximum step is 300
seconds, and it evaluates the resulting path at 5,000 evenly spaced times to
find the closest approach. These are numerical settings, not physical
measurements.

### 6. What “reached the Moon” means here

The model estimates the Moon's Laplace sphere-of-influence (SOI) radius as:

```text
SOI radius = mean Earth–Moon distance × (Moon GM / Earth GM)^(2/5)
```

Here the implementation uses a mean Earth–Moon distance of 384,400 km. If the
propagated path's closest distance to the Moon's center is less than or
equal to that radius, the result is **lunar arrival / SOI entry**. The report
also shows:

```text
SOI margin = SOI radius − closest-approach distance
surface clearance = closest-approach distance − mean lunar radius
```

A positive SOI margin means the modeled path entered the SOI. A negative SOI
margin means it stayed outside. Surface clearance compares the same
closest-approach distance with the Moon's mean radius (1,737.4 km); zero or
negative clearance sets the **surface impact predicted** flag.

That flag is only a closest-distance comparison against a spherical mean
radius. It does not model terrain, vehicle shape, a landing site, braking,
capture, control, or touchdown speed. An impact is not a landing, and an SOI
entry is not proof of capture.

## Showcase scenarios and why they succeed or fail

Use the **Demo scenario** selector in the Mission tab. The four failure
presets below are separate files under `presets/spacecraft/`. Encounter
scenarios use the same lunar-capable vehicle but different transfer durations:
the vehicle preset alone does not determine the Moon's position or the
trajectory geometry.

| Demo scenario | Preset / example inputs | Expected result | Why |
|---|---|---|---|
| Lunar encounter — no surface impact | `lunar_demo.json`; 2026-10-30, 6 days | Enters SOI; closest approach about 1,764.9 km from the center; no mean-surface intersection predicted | The ideal vehicle has enough delta-v and TWR, and this modeled path passes within the SOI but just outside the mean radius. This is not a safe landing. |
| Lunar encounter — surface impact estimate | `lunar_demo.json`; 2026-10-30, 5 days | Enters SOI; closest approach about 427.2 km; mean-radius intersection predicted | Changing transfer duration changes the Moon-target geometry. This path crosses the mean sphere; the model has no terrain or controlled touchdown. |
| Failure — insufficient lift-off thrust | `lunar_low_thrust.json`; 2026-10-30, 5 days | TWR about 0.252; ideal delta-v about 13.52 km/s; launch check fails | Delta-v capacity does not compensate for thrust below loaded vehicle weight. |
| Failure — insufficient Earth-ascent delta-v | `lunar_ascent_shortfall.json`; 2026-10-30, 5 days | TWR about 44.88; ideal delta-v about 6.245 km/s; launch ascent budget fails | It has ample thrust in this simplified check but not the assumed 9.4 km/s ascent budget. |
| Failure — insufficient TLI propellant | `lunar_tli_shortfall.json`; 2026-10-30, 5 days | TWR about 1.764; ideal delta-v about 9.529 km/s; exact TLI about 3.132 km/s, with only about 0.129 km/s left after ascent | It clears the early thrust/ascent gates but cannot afford the computed lunar injection. The trajectory is not propagated. |
| Failure — engine/tank propellant mismatch | `lunar_propellant_mismatch.json`; 2026-10-30, 5 days | Tank loaded with 400,000 kg; usable compatible propellant 0 kg; delta-v 0 km/s | The engine requires LOX/RP-1 while the tank contains LH2/LOX. The incompatible propellant is mass, not usable fuel. |

The exact computed values appear in the Mission report. Minor differences can
result from changing the departure date, transfer duration, or integrator
settings. The encounter numbers above are reference outputs, not universal
guarantees for every date.

## Apollo 11 historical reference profile

The Mission tab includes a separate, fixed Apollo 11 / Saturn V AS-506 reference
profile for the 16 July 1969 launch from LC-39A. Its staging times and selected
parking-orbit/TLI state values come from Tables 2.1 and 2.4 of NASA CR-61291.
The report describes a post-launch operational trajectory; Table 2.1 labels
its event sequence predicted. The profile is therefore a source-backed
historical reference, not raw telemetry and not a prediction generated by this
app. It is intentionally not tied to the currently edited spacecraft.

This improves the project's mission-specific reference data, but does not yet
simulate an Apollo launch vehicle. The available profile does not supply a
complete AS-506 stage mass/propellant ledger, time-varying thrust and mass
flow, atmospheric/aerodynamic model, or guidance law. Those are still required
to numerically predict a launch and compare alternative designs. See
[`LUNAR_DATA.md`](../LUNAR_DATA.md) for the cited anchors and remaining gaps.

### How the designs trade off

- **More propellant** raises the mass ratio in the rocket equation, but also
  raises wet mass and lowers TWR if engine thrust stays fixed.
- **More thrust** raises TWR and can fix a lift-off failure, but does not by
  itself provide enough propellant or ideal delta-v for lunar transfer.
- **More tank capacity is not more delta-v** unless compatible usable
  propellant is actually loaded.
- **Compatible engine and tank propellants** are required for the analysis to
  count fuel as burnable.
- **Passing both vehicle checks is not sufficient for a Moon encounter.** The
  date-specific TLI must also fit, and the propagated path must enter the SOI.
- **A Moon encounter is still not a landing.** A modeled mean-surface
  intersection is an impact estimate, not a safe-touchdown result.

## Model limits to say out loud in a demo

The current model assumes an impulsive Lambert transfer from a selected phase
of a circular 200 km parking orbit. It does not simulate:

- A real launch site, Earth rotation, atmospheric ascent, drag, or gravity
  losses.
- Staging, finite-duration thrust, mass depletion during trajectory
  propagation, engine throttle/restart constraints, or guidance corrections.
- Lunar capture, powered descent, landing-site terrain, landing-gear dynamics,
  touchdown speed, attitude, or safe touchdown.
- Uncertainty ranges, navigation error, or probability of mission success.

The on-screen flight animation illustrates a verdict; it is not the computed
trajectory. Do not present synthetic presets or a green SOI-arrival verdict as
evidence of a buildable spacecraft or a successful lunar landing.
