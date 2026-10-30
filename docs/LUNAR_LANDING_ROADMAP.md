# Lunar Landing Mission: Documentation and Roadmap

## Product goal

The primary workflow is:

**Design a spacecraft → simulate the mission → determine whether it lands safely on the Moon.**

A lunar flyby, impact, sphere-of-influence crossing, or delta-v budget comparison is **not** a successful landing. Those are intermediate events or diagnostics only.

## Definition of success

A run reports **SUCCESS — SAFE LUNAR LANDING** only if the simulated vehicle:

1. Reaches the Moon from its specified departure state using its configured propulsion and propellant.
2. Enters the selected landing region without colliding with terrain before the modeled terminal-descent phase.
3. Touches the lunar surface with touchdown position inside the target site's allowed region.
4. Meets configurable touchdown limits for vertical speed, horizontal speed, attitude/tilt, angular rate, and landing-gear or vehicle clearance.
5. Has a valid continuous trajectory and resource history through touchdown; no required burn is skipped, no propellant goes negative, and no integration/model constraint is violated.

Touchdown limits must be explicit, configurable mission requirements—not hidden assumptions. Initial default limits should be documented and reviewed before being treated as meaningful. Any failed, incomplete, unpowered, or numerically invalid run is **NOT SUCCESSFUL**. Report the reason and the achieved state rather than treating a close approach as a pass.

## Current implementation status

The current mission code is a prototype screening model, not a landing simulator. It uses JPL DE440s for the Sun/Moon states, point-mass Sun/Earth/Moon gravity, an assumed phase-aligned 200 km Earth parking orbit, an impulsive Lambert transfer, an ideal rocket-equation delta-v estimate, and a fixed 9.4 km/s Earth-ascent allowance. Its current `success` result means only that the propagated trajectory enters the Moon's Laplace sphere of influence. `surface_impact` merely flags that the approximate path comes within a mean lunar radius; it does not simulate descent, controlled touchdown, terrain, or landing safety. Therefore the current result must not be presented as a landing success.

## Roadmap

### Phase 0 — Make the outcome contract unambiguous

- Replace the mission result's ambiguous `success` with explicit event/outcome fields, such as `reached_lunar_soi`, `entered_lunar_orbit`, `surface_contact`, `safe_landing`, and a terminal failure reason.
- Keep intermediate milestones visible, but only `safe_landing == true` can produce the success label.
- Store the mission definition with the result: departure epoch, target site and coordinate frame, landing ellipse/region, terminal limits, vehicle configuration/version, data source versions, and model fidelity.
- Add tests proving that flyby, SOI entry, surface impact, hard landing, missed target, fuel exhaustion, and solver failure are not classified as successful landing.

### Phase 1 — Replace placeholder vehicle inputs with a real vehicle definition

For each stage/component, use traceable configuration data for:

- Dry and propellant mass, usable/residual propellant, tank capacity, and stage/engine association.
- Thrust and mass flow as functions of throttle, chamber pressure, and ambient pressure; vacuum/sea-level Isp alone is insufficient for powered flight.
- Throttle range, ignition/restart limits, burn duration, gimbal authority, minimum impulse, and shutdown behavior.
- Vehicle geometry, center of mass/inertia where available, landing gear/contact envelope, and allowable attitude/rates.
- Data source, date/revision, units, uncertainty, and whether values are measured, published, estimated, or illustrative.

**Status:** the data model, provenance tracking, engine operating model (throttle, chamber and ambient pressure), ignition/gimbal limits, mass properties, landing-gear/attitude envelope, and a data-readiness report are implemented (`spacecraft/components.py`, `propulsion.py`, `provenance.py`, `mass_properties.py`, `readiness.py`). No real flight-hardware dataset has been entered yet; all shipped values are `illustrative`.

Do not label catalog/example values as real flight hardware data. Public sources may not expose complete engine maps, residuals, or mass properties for a specific vehicle; missing data must remain an explicit uncertainty or block a high-confidence claim.

### Phase 2 — Model Earth departure and lunar transfer as powered flight

- Define a launch site, Earth-fixed frame, epoch, parking orbit/launch profile, azimuth, and initial vehicle state.
- Include Earth rotation, atmospheric density/winds, aerodynamic forces, gravity losses, finite-duration thrust, mass depletion, staging, and guidance constraints as the vehicle data supports them.
- Use Lambert targeting only as an initial guess or transfer candidate generator; do not treat its impulsive endpoint as the flown trajectory.
- Numerically propagate the commanded burns and coast arcs, then target and correct the arrival state with a shooting/optimization method.
- Track covariance or bounded dispersions for launch timing, thrust, mass, navigation, and maneuver errors; report success probability or margin where justified rather than only a nominal yes/no.

### Phase 3 — Establish a real lunar arrival and landing-site model

- Select a named lunar target site and a documented lunar body-fixed reference frame.
- Use JPL DE440/DE441/SPICE data for solar-system ephemerides, time/frame kernels, and appropriate mission kernels when reconstructing flown trajectories.
- Use lunar gravity products from GRAIL (for example, a suitable GRGM field) at a degree/order appropriate to the desired altitude and accuracy; include mascons and higher-order gravity where they affect the approach.
- Use LRO LOLA topography and an appropriate lunar shape/terrain model for elevation, slope, hazards, and local surface-normal calculations. LROC imagery and archived landing-site products can support visual/hazard constraints but do not replace terrain geometry.
- Include lunar rotation/orientation, solar radiation pressure if it matters for the vehicle/flight time, and third-body perturbations as appropriate.
- Validate ephemeris and gravity-model coverage at every requested epoch/altitude; fail clearly outside supported ranges.

### Phase 4 — Add powered descent and touchdown dynamics

- Model braking, approach, and terminal descent as finite burns with vehicle mass changing throughout the burn.
- Add guidance laws and flight-control limits: throttle response, gimbal/attitude control, sensor/navigation error, actuator saturation, and engine restart constraints.
- Propagate 6-DOF vehicle state when mass properties and control data are available; otherwise clearly identify a lower-fidelity point-mass descent model.
- Detect terrain contact using the vehicle/landing-gear envelope against local terrain, not a mean lunar radius alone.
- Distinguish safe touchdown, hard landing, tip-over, terrain collision, fuel exhaustion, and missed site as separate terminal outcomes.

### Phase 5 — Verify against known cases and uncertainty

- Build unit tests for conservation/invariants, atmosphere interpolation, mass depletion, stage events, frame/time transforms, gravity, terrain contact, and touchdown limits.
- Compare mission phases with trusted published mission reconstructions and NASA/JPL SPICE kernels where compatible and available. Validate states in the same frame and time scale; do not compare unlike orbit definitions or use rounded public summaries as precision truth data.
- Add regression cases for successful and failed landings, including dispersions and boundary conditions.
- Run sensitivity/Monte Carlo cases and show which input uncertainties dominate landing probability.
- Record software version, kernels, gravity/terrain model versions, vehicle data revision, solver tolerances, and configuration with every result for reproducibility.

## Candidate authoritative data and tools

- [JPL planetary and lunar ephemerides](https://ssd.jpl.nasa.gov/planets/eph_export.html) — DE440/DE441 state data and details.
- [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/) — independent ephemeris queries for selected epochs and objects.
- [NAIF SPICE kernels](https://naif.jpl.nasa.gov/naif/data.html) — SPK, PCK, LSK, and mission-specific kernels; choose kernels that match the mission and coverage.
- [JPL planetary physical parameters](https://ssd.jpl.nasa.gov/planets/phys_par.html) and [NASA Moon Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html) — reference constants, not a substitute for high-resolution gravity or shape fields.
- [NASA Planetary Data System Geosciences Node: LRO](https://pds-geosciences.wustl.edu/missions/lro/) — archived LRO products, including LOLA and radio-science datasets; use gravity products derived from GRAIL for lunar gravity.
- [NASA NTRS](https://ntrs.nasa.gov/) and mission/PDS archives — published mission design, reconstruction, hardware, and validation material. Confirm the configuration and provenance of each value before use.
- Astropy provides unit-aware times, coordinates, and constants; SciPy provides numerical integration/optimization primitives. They are implementation tools, not sources of vehicle truth or validated landing logic.

## First implementation milestone

The next meaningful milestone is **not** adding more constants to the existing flyby check. It is to:

1. Create a versioned mission/vehicle configuration with stages, thrust curves, propellant loads, and a target landing site.
2. Change the UI outcome to show **SIMULATED / FAILED / SAFE LANDING**, with SOI entry and impact as intermediate events only.
3. Implement finite-burn Earth departure and lunar transfer using the configured vehicle.
4. Add a low-altitude powered-descent model and terrain-contact criterion with explicit touchdown limits.
5. Verify the pipeline against at least one documented lunar landing trajectory and clearly state what vehicle/telemetry data is still unavailable.

Until these criteria and validation gates are met, all results should be labeled **prototype estimates**, not claims that a spacecraft can land on the Moon.
