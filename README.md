# Spacecraft Configurator

An interactive spacecraft configuration designer. A DearPyGui panel edits the
vehicle (engines, propellant tanks, payloads, power systems) and an OpenGL
viewport shows it live in 3D. Mass, ideal delta-v, TWR, burn time, and power
balance update as the design changes, and a lunar-reachability check propagates
the vehicle against the JPL DE440s ephemeris.

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
verified masses and engine performance for meaningful results.

The product's actual success goal is a safe lunar touchdown. See
[docs/LUNAR_LANDING_ROADMAP.md](docs/LUNAR_LANDING_ROADMAP.md) for the success
definition, current-model limits, required real-world data, and implementation
roadmap.

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

## Project structure

```text
app.py                   Entry point
spacecraft/              Domain model (no UI/GL imports)
  components.py          Engine, FuelTank, Payload, PowerSystem + illustrative catalog
  propulsion.py          Throttle, ignition/restart, gimbal data
  provenance.py          Data source/quality/uncertainty records
  vehicle.py             Spacecraft assembly, landing gear, attitude limits
  mass_properties.py     Mass, centre of mass, inertia, static tip-over angle
  readiness.py           Reports missing/untraceable vehicle data
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
