# Spacecraft Configurator

An interactive spacecraft mission-design and analysis platform. A DearPyGui panel edits the
vehicle (engines, propellant tanks, payloads, landing legs, RCS thrusters, solar
arrays, batteries, and avionics) and an OpenGL viewport shows it live in 3D.
Mass, ideal delta-v, TWR, burn time, and installed power ratings update as the
design changes, and a lunar-reachability check propagates the vehicle against
the JPL DE440s ephemeris.

## Viewport controls

| Input | Action |
| --- | --- |
| Left-drag | Orbit |
| Right- or middle-drag | Pan |
| Mouse wheel | Zoom |
| Left-click a part | Select it (highlighted in the viewport and the component list) |
| `F` | Frame the vehicle |
| `R` | Reset the camera |

The designer panel adds components, edits their properties, duplicates parts
(handy for engine clusters), saves/loads the design as JSON, and has an
**Exploded view** slider and grid toggle. Part sizes follow the design:
tank length tracks propellant capacity, engine bell size tracks thrust, and
solar-wing area tracks generation. This is a visualization aid, not CAD.
Each part can be freely positioned or attached to another component, with
XYZ offsets, Euler rotations, selectable attachment nodes, reset controls,
and X/Z mirror-copy actions. **Frame the vehicle** and initial camera framing
include manually placed parts.

Landing gear, RCS, solar arrays, batteries, and avionics contribute their
declared dry masses to vehicle metrics. Installed solar generation, battery
capacity and charge/discharge ratings, and avionics/RCS electrical loads are
shown in the power summary. These are nameplate values, not a time-dependent
power simulation: illumination, pointing, state of charge, RCS propellant
consumption, landing contact, and landing-leg loads are not simulated. RCS
thrust is reported separately and does not count as main-engine thrust or
delta-v.

## Mission Design Constraints

The mission check is a single-stage screening, and it is strict. The vehicle needs
thrust-to-weight above 1 to leave the pad, and about 12.6 km/s of ideal delta-v
(9.4 km/s Earth ascent plus about 3.2 km/s transfer). The two pull against each other:
adding propellant raises delta-v but lowers thrust-to-weight. With the catalog engine
(845 kN, 300 s Isp) only a narrow band of designs passes: too little fuel or thrust
falls short, too much fuel for the engines cannot lift off.

The app opens with the **Lunar Demo** loaded. It passes the current single-stage
reachability checks (liftoff thrust-to-weight and ideal delta-v for Earth ascent plus
lunar transfer), so you can run the trajectory screening immediately. The **Lunar
mission check** shows both numbers as you edit the design. This preset is illustrative,
not flight hardware: its engine thrust and tank mass are deliberately unrealistic. A
passing check is not proof that a real spacecraft can fly or land on the Moon.

## Mission flight animation

**Run Lunar Mission Simulation** also animates the viewport and shows a verdict
banner above it. The vehicle lifts off and hovers while the simulation runs in
the background, then the verdict decides what happens:

| Verdict | Animation | Banner |
| --- | --- | --- |
| Path reaches the Moon | Flips tail-first, retro-burns, and lands softly on the white Moon sphere | `REACHED THE MOON` (green) |
| Path misses the Moon | Flies past the Moon and is lost in space | `MISSION FAILED — misses the Moon`, with closest approach |
| Vehicle cannot reach it (delta-v) | Engine sputters out, the vehicle falls back and crashes | `MISSION FAILED — cannot reach the Moon`, with the reason |
| Cannot lift off (thrust-to-weight not above 1, or no engine) | Engine strains on the pad; the vehicle never leaves | `MISSION FAILED — cannot lift off`, with the reason |
| Simulation error (e.g. offline) | Returns to the pad | `SIMULATION ERROR — no verdict` (amber) |

Editing the design, or **Reset Flight**, returns the vehicle to the pad. The
animation illustrates the verdict; it is not a plot of the computed trajectory.
"Reached the Moon" still only means the path entered the Moon's sphere of
influence: capture, descent and touchdown are not simulated, so the landing is
an illustration and the banner says so.

## Lunar mission screening

**Run Lunar Mission Simulation** takes a UTC departure date and transfer
duration, solves a Lambert transfer, then numerically propagates the spacecraft
with Sun/Earth/Moon gravity against JPL DE440s. It reports whether the
trajectory reaches the Moon's sphere of influence, the required injection
delta-v, closest approach, and predicted surface impact. The DE440s kernel is
downloaded on first use and cached locally.

This is trajectory screening, not capture or landing. It assumes a 200 km
circular parking orbit, impulsive injection, a 9.4 km/s Earth-ascent allowance,
and ideal rocket-equation delta-v. Catalog values are illustrative; enter
verified masses and engine performance for meaningful results. After each run,
the Mission tab reports vehicle mass/thrust/TWR, the complete delta-v budget and
margins, closest-approach distance/time, lunar sphere-of-influence margin,
relative speed at closest approach, estimated surface clearance, integrator
settings, data source, and model assumptions. Failed runs
include their blocking checks or measured miss distance and the run inputs that
affect the modeled encounter. These diagnostics describe this model; they are
not flight-validated failure predictions.

## Apollo 11 historical reference

The Mission tab also includes a fixed Apollo 11 / Saturn V AS-506 reference
profile for 16 July 1969 from LC-39A. It exposes NASA CR-61291 launch, staging,
parking-orbit, and TLI event/trajectory summary values. This is a source-backed
historical reference, not a live simulation or raw-telemetry reconstruction:
the source labels its event sequence predicted and does not provide the
complete Saturn V stage mass, engine, aerodynamic, or guidance data needed to
predict alternate designs. Keep it separate from the configurable Lunar Demo
and JPL lunar-encounter screening.

The product's actual success goal is a safe lunar touchdown. See
[docs/LUNAR_LANDING_ROADMAP.md](docs/LUNAR_LANDING_ROADMAP.md) for the success
definition, current-model limits, required real-world data, and implementation
roadmap.

For a plain-language explanation of the equations, mission checks, and
selectable failure/encounter examples, see
[docs/LUNAR_MISSION_PHYSICS_AND_DEMO_SCENARIOS.md](docs/LUNAR_MISSION_PHYSICS_AND_DEMO_SCENARIOS.md).

For a beginner-friendly, step-by-step guide to running and presenting the app,
see the [Spacecraft Configurator Beginner's Demo Manual](docs/BEGINNER_DEMO_MANUAL.md).

## Vehicle definition

Every component and the vehicle itself carry a **data provenance** record:
`quality` (`measured`, `published`, `estimated`, or `illustrative`), `source`,
`revision`, `uncertainty_pct`, and units. `measured`/`published` data must cite a
source. Everything built from the catalog is `illustrative`.

Optional values default to `None`, which means *unknown*, never zero. The
**Vehicle data readiness** panel lists what is unknown or untraceable and labels
the vehicle `PROTOTYPE DATA` until nothing blocks and every part cites real data.
Definitions cover:

- Mass: dry, loaded and residual propellant, tank capacity, stage assignment.
- Engines: vacuum thrust/Isp, sea-level thrust or exit area, chamber pressure,
  throttle range and curve, ignition/restart limits, burn duration, minimum
  impulse, tail-off, gimbal angle and rate. `Engine.thrust_at(throttle,
  ambient_pressure_pa)`, `mass_flow_at` and `chamber_pressure_at` evaluate the
  model and raise `MissingDataError` rather than guess.
- Geometry: component envelopes, centre of mass and inertia, landing-gear contact
  envelope, allowable tilt and angular rate.

The panel edits stage, data quality/source and residual propellant. The rest is
set in the JSON design file (schema v2; v1 files still load).

## Apollo LM reference vehicle

**Load Apollo LM** loads the Apollo Lunar Module descent stage
([presets/spacecraft/apollo_lm.json](presets/spacecraft/apollo_lm.json)), built
from [LUNAR_DATA.md](LUNAR_DATA.md). Its ideal descent delta-v (2,033 m/s) agrees
with the published 2,004 m/s budget to 1.4%. Only values the data package
supports are entered, as `estimated` until checked against primary sources; the
readiness panel still blocks on the two items the package could not find
(allowable touchdown tilt/rate and engine ground clearance). The suspect
4,932 kg Apollo 11 touchdown mass is deliberately not used.

`spacecraft/reference_data.py` holds the Apollo 11 site, GRGM1200A gravity,
SLDEM2015 terrain, descent profile, proposed touchdown limits, touchdown
reconstructions, and the data-gap register, each with provenance. The
simulation does not consume them yet.

## Project structure

```text
app.py                   Entry point
spacecraft/              Domain model (no UI/GL imports)
  components.py          Propulsion, structure, power, avionics + illustrative catalog
  propulsion.py          Throttle, ignition/restart, gimbal data
  provenance.py          Data source/quality/uncertainty records
  vehicle.py             Spacecraft assembly, landing gear, attitude limits
  mass_properties.py     Mass, centre of mass, inertia, static tip-over angle
  readiness.py           Reports missing/untraceable vehicle data
  apollo_lm.py           Apollo LM reference vehicle builder
  reference_data.py      Apollo 11 site, gravity, terrain, descent, validation data
  analysis.py            Ideal performance and mission budgets
  geometry.py            3D layout: primitive meshes + per-part transforms
  mission.py, lunar.py   Lambert transfer + ephemeris propagation
  presets.py             JSON save/load
viewport/
  orbit_camera.py        Turntable camera
  spacecraft_viewport.py Draws the layout, grid, highlight; picking
rendering/
  opengl_renderer.py     Offscreen moderngl renderer (MSAA, lit meshes, ID picking)
ui/
  designer_application.py  Wires panel, input, viewport, renderer
  spacecraft_designer.py   Designer panel
  dpg_input_source.py      Mouse/scroll state for the viewport image
  layout.py, application.py DearPyGui window and viewport setup
core/                    Event bus, performance monitor
presets/spacecraft/      Starter design
tests/
```

The renderer draws into an offscreen framebuffer and uploads it to a DearPyGui
dynamic texture each frame. Picking re-renders component IDs into a second
buffer only when the cursor moves or clicks.

## Setup

Requires Python 3.11 and a GPU/driver with OpenGL 3.3.

```powershell
.\setup.ps1   # create .venv and install requirements
.\run.ps1     # launch the configurator
.\test.ps1    # run the tests
```

On macOS/Linux use `setup.sh`, `run.sh`, and `test.sh`.

See [docs/LUNAR_LANDING_ROADMAP.md](docs/LUNAR_LANDING_ROADMAP.md) for the
project's definition of a successful lunar landing and the fidelity roadmap.
