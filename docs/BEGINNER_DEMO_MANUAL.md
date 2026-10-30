# Celeste SpaceWorks: Beginner's Demo Manual

This guide is for people seeing spacecraft design for the first time. It
explains what the application is for, how to run a short demonstration, what
the main numbers mean, and what not to claim from the results.

> **Important:** Celeste SpaceWorks is an interactive spacecraft mission-design and analysis platform for engineering exploration and education. The platform combines representative spacecraft models with real astronomical data, including JPL DE440 ephemerides and historical mission references. Mission results should be interpreted as engineering-screening outcomes rather than flight certification, operational mission approval, or landing validation.


## 1. What is this project?

Celeste SpaceWorks is an interactive spacecraft mission-design and analysis platform that combines spacecraft assembly, engineering evaluation, 3D visualization, and Earth-to-Moon mission screening in a single workflow.

Users can design a spacecraft, evaluate mass, propulsion, power, and stability characteristics, and then explore how those decisions affect mission feasibility.

The platform connects vehicle design and mission analysis so that engineering tradeoffs can be understood in a visual and interactive environment.

The app brings several questions into one place:

- **What is the vehicle made of?** Add an engine, propellant tank, payload,
  landing gear, attitude-control thrusters, solar panels, batteries, and
  avionics.
- **How heavy is it?** Component and propellant masses are added into dry and
  loaded vehicle mass.
- **Can the main engine lift this example vehicle?** The app compares main
  engine thrust to the vehicle's weight using a simple thrust-to-weight ratio.
- **Does the idealized propellant budget cover the trip?** An ideal rocket
  equation estimates the speed change, called delta-v, available from the
  engine and compatible propellant.
- **Why might a design fail?** The pre-checks and mission report expose
  constraints such as insufficient thrust, insufficient delta-v, incompatible
  propellant, or missing lunar encounter.
- **How do components fit together?** The 3D view and placement editor make
  assembly layout easier to see and adjust.
- **What data is still unknown?** Data readiness and provenance fields make
  the difference between published, estimated, and  inputs
  visible.

### Why is that relevant?

Space missions are systems problems. A change to one part can affect other
parts: more propellant can increase ideal delta-v, but it also adds mass; more
thrust can improve liftoff margin, but thrust alone cannot replace a missing
propellant budget. Power hardware and landing gear add useful capabilities
while also adding mass. A spacecraft is not just an engine or a destination:
the pieces have to fit together and the mission has to satisfy several
constraints.

This project helps a group **visualize those relationships**, practice asking
good engineering questions, and explain why a result succeeds or fails under
the model. It also provides a place to discuss how assumptions and data quality
affect conclusions. It does not answer whether a proposed real spacecraft is
safe, buildable, or ready to fly.

## What uses real-world data?

The mission environment incorporates several real-world datasets and references:

- JPL DE440 ephemerides
- Date-specific Earth-Moon geometry
- Date-specific Moon and Sun positions
- Lambert transfer calculations
- Numerical trajectory propagation
- Apollo 11 mission-reference data
- Kennedy Space Center LC-39A historical launch-site reference

Vehicle components use representative engineering models intended for design-space exploration and mission screening.

## 2. Start the application

From the project directory, run:

```bash
python app.py
```

If your group uses the project's virtual environment, use its Python
executable instead, for example:

```bash
.venv/bin/python app.py
```

The main window contains the **Spacecraft Designer** panel and the 3D
viewport. The panel has **Design**, **Analysis**, and **Mission** tabs. The app
normally opens with the **Lunar Demo** preset already loaded.

The first lunar mission run may need to download the JPL DE440s ephemeris
kernel (a data file describing planetary positions). Internet access may be
needed for that first download. Allow time for it to complete. If the run
reports an error, treat that as a simulation/data error—not evidence that the
spacecraft failed.

## 3. A short demo run-through

This run-through is designed for a live presentation. It starts with the
already loaded Lunar Demo, shows the design and analysis, then runs a repeatable
encounter scenario.

### Step A: Introduce the vehicle

1. Start on the **Design** tab.
2. Point out the component list and the 3D spacecraft.
3. Say: “This is an  spacecraft assembled from editable parts. Its
   numbers are chosen to demonstrate the software's checks; they are not
   specifications for real flight hardware.”
4. Click **Lunar Demo** if you want to restore the starting example.

### Step B: Show the assembly

1. Drag with the **left mouse button** over the viewport to orbit the camera.
2. Use the **mouse wheel** to zoom.
3. Drag with the **right or middle mouse button** to pan.
4. Click a component in the viewport or component list to select it. The
   selected part is highlighted and its properties appear in the inspector.
5. Move the **Exploded view** slider to separate the stacked sections. Return
   it to zero to restore the assembled view.
6. Use **Grid** to show or hide the reference grid. Use **Reset Camera** (or
   press `R` while the cursor is over the viewport) to reset the camera. Press
   `F` over the viewport to frame the vehicle.

The 3D shapes are schematic visualizations, not manufacturing drawings. Their
size and arrangement are intended to make parts identifiable, not to establish
real clearances or structural dimensions.

### Step C: Explain the design numbers

1. Open **Analysis**.
2. Read the mass, thrust, delta-v, thrust-to-weight, burn-time, and power
   summary out loud using the glossary in section 5.
3. Show the **Mass by component** plot. It separates component dry mass from
   loaded propellant.
4. Show the **Delta-v vs mission budget** plot. It compares an ideal estimate
   from this vehicle with approximate mission budgets.
5. Point out **Lunar mission check** and **Vehicle data readiness**. The first
   shows whether the example clears the initial screening gates; the second
   reminds the audience whether the inputs are complete and traceable.
6. Point to **Mission Screening Verdict** and the configuration screening bar.
   The score counts five displayed checks equally: liftoff, ideal delta-v,
   positive declared power margin, known center of mass, and traceable
   definition data. It is explicitly not a flight-readiness percentage.
7. Point to **Vehicle Health** for a compact delta-v, TWR, power-margin, and
   stability snapshot. “Unknown” stability means the required data is not
   present; it does not mean stable.

These are screening estimates. In particular, a bar that reaches a budget
does not prove a real mission is feasible: the model omits important real
flight effects described in section 7.

### Step D: Run a repeatable lunar encounter

1. Open **Mission**.
2. In **Demo scenario**, select **Lunar encounter — no surface impact**.
3. Click **Load demo scenario**. This loads the demo vehicle preset and sets the
   example departure date and transfer time.
4. Confirm the date shown is `2026-10-30` UTC and the transfer time is `6` days.
5. Click **Run Lunar Mission Simulation**.
6. Wait for the run to complete. Read the status, details, and mission
   timeline. In the 3D view, the verdict animation is an illustration of the
   result, not a plot of the calculated path.
7. Explain that this scenario demonstrates modeled lunar sphere-of-influence
   entry without an intersection with the Moon's mean-radius surface for these
   inputs. It does not demonstrate lunar orbit or a safe landing.

The example inputs are fixed for the showcase. If you change the date or
transfer time, use the new on-screen report as the result; don't promise the
same closest approach. The DE440s data is date-specific and the mission
geometry changes with the inputs.

### Step E: Demonstrate one failure

1. Keep the **Mission** tab open.
2. Select **Failure — insufficient lift-off thrust**.
3. Click **Load demo scenario**, then **Run Lunar Mission Simulation**.
4. Point to the low thrust-to-weight value and the failure reason. Explain:
   “Having enough ideal delta-v on paper does not help if the engine cannot
   overcome the vehicle's weight in the model.”

For a quick comparison, reload **Lunar encounter — no surface impact** and
run it again. The contrast is more useful than presenting a failure as simply
“bad design”: each scenario isolates a particular constraint.

## 4. Tabs and controls

### Design tab

The **Design** tab is where you assemble and arrange the spacecraft.

At the top, use **Choose a preset** and **Load preset** to quickly switch
between the Lunar Demo, Apollo Lunar Module reference vehicle, starter design,
and individual failure examples. Selecting an option only previews it; click
**Load preset** to replace the current in-memory design. The status text
confirms which preset loaded. This does not change the file used by **Save
Design** or **Load Saved Design**. Those buttons operate on the current save
path, while built-in presets are loaded independently. The older **Lunar Demo**
and **Load Apollo LM** buttons remain as one-click shortcuts.

**Add component** buttons create a new part with an editable 
starting value:

| Button | What it represents |
| --- | --- |
| **Engine** | Main propulsion that provides the thrust used in the basic launch and delta-v estimates. |
| **Tank** | Stores propellant; loaded mass and propellant type affect the vehicle mass and usable fuel. |
| **Payload** | The equipment, cargo, or mission item carried by the vehicle. |
| **Power** | Legacy combined power-system entry with generation and storage ratings. |
| **Landing gear** | A multi-leg landing-gear assembly shown in the 3D view. |
| **RCS** | Reaction-control thrusters for small attitude-control maneuvers; not counted as main-engine performance. |
| **Solar panel** | A deployable array with area and rated generation. |
| **Battery** | Electrical energy capacity and maximum charge/discharge power ratings. |
| **Avionics** | Guidance, navigation, and control electronics with a declared power load. |

Select a part to inspect it. Depending on the component, the inspector allows
you to edit its name, dry mass, hardware-specific fields, stage, data quality,
source, center-of-mass inputs, and placement. Invalid values are rejected and
the previous valid value is restored.

The **Vehicle Architecture** card summarizes component assemblies, installed
cluster counts (for example, individual RCS thrusters and landing legs), stage
numbers, and the selected mission target. When a component is selected, the
viewport header also shows its name, mass, and relevant hardware ratings.

After editing a numeric component property, the inspector's **Change Impact**
readout compares the modeled vehicle metrics with their values before that
edit. It reports changes such as mass, main/RCS thrust, ideal delta-v, TWR, and
power margin. It is an immediate before/after comparison, not a prediction of
the whole mission. A placement-only change may correctly show no change to
these mass/performance numbers.

#### Placement controls

- **Automatic layout** lets the application arrange the part in its schematic
  stack.
- **Free placement** positions it in the vehicle coordinate frame.
- **Attach to ...** anchors it to another part using selectable parent and part
  nodes.
- **X/Y/Z (m)** fields set position offsets in metres. In free placement they
  are vehicle-frame offsets; for attached parts they are in the parent frame.
- **RX/RY/RZ (deg)** fields set local Euler rotations, in degrees.
- **Return to automatic layout** removes explicit placement.
- **Reset rotation** sets the local rotation back to zero.
- **Mirror copy X/Z** creates another component reflected across the chosen
  axis. It is a new part, so its mass and subsystem ratings are counted again.

The editor helps with visual arrangement; it does not detect collisions,
validate attachment strength, route cables, or simulate panel deployment.
When moving a component, press `F` over the viewport if you need to bring the
new overall assembly into view.

**Save Design** and **Load Saved Design** use the current preset path. In the
default setup, that path is the bundled `presets/spacecraft/lunar_demo.json`.
Be careful: using **Save Design** while working on the default design can
overwrite that file. For a presentation, the safest option is to demonstrate
without saving, or make a separate copy of the preset before editing it
outside the app. **Clear Assembly** removes all parts from the current
in-memory design; **Lunar Demo** restores the  lunar example.

### Analysis tab

The **Analysis** tab summarizes the currently edited assembly:

- **Dry mass** is the sum of component masses without loaded tank propellant.
- **Fuel mass** is the usable propellant the analysis can match to the installed
  engine fuel type.
- **Wet mass** is component dry mass plus all loaded tank propellant, including
  incompatible propellant.
- **Thrust** is the installed main-engine thrust used by the basic performance
  model.
- **RCS thrust** is shown separately as auxiliary thrust; it is not included in
  main-engine thrust, thrust-to-weight, or delta-v.
- **Delta-v** is the idealized speed-change budget calculated from engine
  specific impulse and usable compatible propellant.
- **TWR** (thrust-to-weight ratio) compares main-engine thrust with loaded
  vehicle weight in the simplified liftoff check.
- **Burn time** is an ideal estimate based on propellant mass and main-engine
  mass flow.
- **Power** reports installed generation, declared load, surplus/deficit,
  storage capacity, and maximum charge/discharge ratings.
- **Center of mass** and **Static tip-over limit** are shown only when the
  relevant center-of-mass and spacecraft landing-gear data are available.
- **Mass by component** and **Delta-v vs mission budget** are comparison plots.
- **Mission assessment**, **Lunar mission check**, and **Vehicle data
  readiness** provide screening status, warnings, and data gaps.

Component power ratings are not a live power simulation. The app does not
calculate panel illumination or pointing, battery state of charge, power
histories, or a redundant avionics load multiplier. Enter avionics power draw
as the total load you want the summary to represent.

### Mission tab

The **Mission** tab contains two different references and a trajectory screen:

- **Earth → Moon · Apollo 11 launch-site reference** shows Kennedy Space
  Center's LC-39A coordinates from the historical reference. This is
  presentation context only: the current transfer calculation does not use a
  launch site or simulate a surface launch.
- **Apollo 11 historical reference · AS-506** is a fixed, source-backed
  historical profile. Expand it to see the report. It is not connected to the
  currently edited vehicle and is not a Saturn V simulation.
- **Demo scenario** loads a preset plus example date and transfer duration.
- **Mission target** changes the mission-budget comparison used in Analysis; it
  does not change the lunar trajectory solver's target.
- **Departure date (UTC)** selects the date used for date-specific ephemeris
  positions. Enter it as `YYYY-MM-DD`.
- **Transfer time (days)** is the assumed travel duration; the input is limited
  to 3–8 days.
- **Run Lunar Mission Simulation** runs the lunar trajectory screen.
- **Status**, **details**, and **Mission timeline** show the run stage and
  outcome.
- **Mission Status · Model Milestones** presents launch, Earth orbit, TLI,
  arrival, and landing as high-level status labels. “Screened” launch/orbit/TLI
  steps represent assumptions and budget checks; they are not simulated
  launch events. A lunar arrival never marks safe landing as passed.
- **Failure guidance** summarizes a suggested next check. Use the complete
  failure reasons and vehicle warnings in the report to understand the result;
  guidance is a starting point, not an automatic design fix.

Changing the spacecraft or mission inputs invalidates a previous result. Run
the mission again after making changes.

## 5. Space words in plain English

| Term | Plain-language meaning |
| --- | --- |
| **Spacecraft / vehicle** | The whole assembled machine being considered. |
| **Component** | One part in the assembly, such as a tank, engine, battery, or payload. |
| **Dry mass** | The mass of a component or vehicle without usable loaded propellant. |
| **Propellant** | The material an engine expels to produce thrust. It is both fuel for the engine and mass the vehicle must carry. |
| **Thrust** | A push, measured in newtons. Main-engine thrust is the push used in the simplified liftoff check. |
| **Specific impulse (Isp)** | A measure of how efficiently an engine uses propellant. In this model, a larger value generally gives more ideal delta-v for a given mass ratio. |
| **Delta-v (Δv)** | “Change in velocity,” usually shown in metres per second or kilometres per second. It is a budget of how much the vehicle could change its speed in an idealized calculation. |
| **Thrust-to-weight ratio (TWR)** | Main-engine thrust divided by the vehicle's weight. Below 1 means the simplified check says thrust is too small to lift off vertically. |
| **Burn time** | An ideal estimate of how long the loaded usable propellant could flow at the modeled engine rate. It does not include real start-up, shutdown, throttle, or trajectory effects. |
| **Earth ascent** | The difficult part of traveling from Earth's surface to space. Here it is represented by a fixed approximate delta-v allowance, not a simulated launch. |
| **Parking orbit** | A temporary orbit around Earth. The trajectory screen assumes a circular orbit 200 km above Earth. |
| **TLI** | Trans-lunar injection: the maneuver that sends a spacecraft from an Earth parking orbit toward the Moon. The screen treats it as an instantaneous ideal burn. |
| **Ephemeris** | A table/model of where celestial bodies are at particular times. The lunar simulation uses JPL DE440s for the Moon and Sun positions. |
| **Sphere of influence (SOI)** | A convenient approximate boundary where the Moon's gravity becomes important to the modeled spacecraft path. Entering the SOI is not the same as orbiting or landing on the Moon. |
| **RCS** | Reaction-control system: smaller thrusters used to turn or make small adjustments. This app displays their ratings but does not use them to change the lunar path. |
| **Avionics** | The electronics used for navigation, control, and spacecraft management. |
| **Data provenance** | A record of where a number came from and whether it is measured, published, estimated, or . |

## 6. Demo scenario guide

All built-in scenarios use the date `2026-10-30` UTC. The encounter scenarios
also use fixed transfer times to make a repeatable presentation. Results can
change if you edit the date, transfer duration, or vehicle.

| Scenario | What to point out |
| --- | --- |
| **Lunar encounter — no surface impact** | Six-day transfer using the Lunar Demo. The reference result enters the Moon's SOI without intersecting the Moon's mean-radius surface. This is a modeled encounter, not orbit insertion or landing. |
| **Lunar encounter — surface impact estimate** | Same vehicle, five-day transfer. The reference path intersects the Moon's mean-radius sphere. The result is an impact estimate, not evidence of a safe touchdown. |
| **Failure — insufficient lift-off thrust** | The TWR is below 1. The vehicle cannot lift vertically in the simplified check, even if its ideal delta-v is large. |
| **Failure — insufficient Earth-ascent delta-v** | The vehicle's ideal delta-v does not cover the approximate 9.4 km/s ascent allowance. Strong thrust cannot compensate for too little ideal speed-change budget. |
| **Failure — insufficient TLI propellant** | It clears the early ascent checks, but lacks enough remaining ideal delta-v for the selected date's TLI requirement. |
| **Failure — engine/tank propellant mismatch** | The tank contains propellant that does not match the engine's declared fuel type. It still adds vehicle mass but is not counted as usable compatible fuel. |

The exact current measurements and failure explanations appear in the
on-screen report. Treat the values in the table as reference expectations, not
guarantees after changing the inputs.

## 7. What the model does—and does not—say

The lunar trajectory screen uses a Lambert transfer calculation and then
numerically propagates an idealized path under simplified Sun, Earth, and Moon
gravity. It uses JPL DE440s body positions for the selected date. The result
reports trajectory and encounter quantities such as required injection
delta-v, closest approach, and whether the path enters the estimated lunar
SOI.

Here are the current limitations when showing success:

- The 9.4 km/s Earth-ascent figure is a fixed allowance, not an Earth launch
  simulation. There is no launch site, atmosphere, drag, Earth rotation,
  steering, or gravity-loss model.
- The 200 km circular parking orbit and TLI are assumptions. TLI is treated as
  an impulsive burn; engine burn duration, vehicle mass depletion, and
  mid-course corrections are not used in the propagated path.
- The model does not calculate lunar capture, a stable lunar orbit, powered
  descent, landing-site terrain, a landing burn, or touchdown.
- A predicted mean-surface intersection means the path reaches the modeled
  lunar radius. It is not a simulated landing, safe or otherwise.
- Landing legs and power/RCS subsystems are represented as configurable parts
  and ratings. They do not control or support the simulated trajectory.
- The animation illustrates the final verdict. It is not the computed
  trajectory or a real-time animation of the vehicle's orbital state.
- The Apollo 11 panel is a separate fixed historical reference from NASA
  CR-61291. The source provides selected event and trajectory values, not the
  complete Saturn V data needed to predict a new launch or alternative design.
- The built-in catalog and Lunar Demo contain synthetic  values.
  A successful result is not flight evidence.

For the detailed equations and model assumptions, see
[Lunar Mission Demo: Physics, Math, and Example Designs](./LUNAR_MISSION_PHYSICS_AND_DEMO_SCENARIOS.md).
For the longer-term requirements for a realistic landing model, see
[Lunar Landing Roadmap](./LUNAR_LANDING_ROADMAP.md).

## 8. Suggested presenter script

This script takes about five minutes. It can be split among several presenters.

**Presenter 1 — Purpose (about 30 seconds)**

> “This project makes spacecraft design tradeoffs visible. We can assemble
> components, see how mass and propellant affect ideal performance, and test
> why a simplified mission screen passes or fails. The values in this demo are
> , so this is a learning tool—not a flight design.”

**Presenter 2 — Design (about one minute)**

> “This is the Lunar Demo assembly. Each part contributes mass, and the 3D
> view helps us see how the parts fit. We can select a part to inspect it,
> change its position, or add subsystems like landing legs, batteries, and
> avionics. The geometry is schematic, not construction-ready.”

**Presenter 3 — Analysis (about one minute)**

> “The two important early checks are thrust-to-weight and delta-v. TWR asks
> whether the engine's push is greater than the vehicle's weight. Delta-v is
> the ideal speed-change budget from the engine and compatible propellant.
> More propellant may increase delta-v, but it also makes the vehicle heavier.
> These checks explain tradeoffs; they don't simulate a real launch.”

**Presenter 4 — Mission and failure (about two minutes)**

> “We load a fixed-date lunar encounter and run the trajectory screen. A green
> encounter only says the modeled path entered the Moon's approximate sphere
> of influence. It is not capture or landing. Now we load the low-thrust
> failure. Its delta-v can look promising, but its thrust-to-weight is below
> one, so the simplified vehicle cannot lift off. The different outcomes show
> why mission design needs several checks, not just one large number.”

**Closing (about 30 seconds)**

> “The project is relevant because it helps people reason about connected
> spacecraft constraints and communicate uncertainty. The next step toward a
> true landing simulation would require validated vehicle data, launch and
> propulsion models, lunar capture and descent guidance, terrain, and
> touchdown dynamics.”

## 9. Quick troubleshooting

| What you see | What to do |
| --- | --- |
| The vehicle is too small, off-screen, or awkwardly framed | Hover over the viewport and press `F`, or click **Reset Camera**. Use the wheel to zoom and right/middle drag to pan. |
| A component did not get selected | Left-click the part without dragging. You can also click its name in the component list. |
| A changed mission still shows old inputs or no result | Choose **Load demo scenario** to restore its inputs, or re-enter the departure date and transfer time, then run again. |
| The mission takes time on its first run | The ephemeris data may be downloading or loading. Wait for completion before starting another run. |
| The run reports an error | Read the status/details. An error is not a vehicle failure; check data download/network availability and try again. |
| A design shows a warning or fails a check | Read the reason in Analysis or the Mission report. Check compatible engine/tank propellant, loaded fuel, thrust-to-weight, and the remaining delta-v. |
| You want to restore the original example | Click **Lunar Demo**. This loads the in-memory design; it does not undo a file already overwritten with **Save**. |
| The power summary shows a deficit | Compare the installed generation and declared loads. It is a rating comparison, not proof of a real-time power outage or proof that a battery can cover a mission timeline. |

## 10. Helpful files

- [README](../README.md) — project overview and main feature summary.
- [Physics and demo scenarios](./LUNAR_MISSION_PHYSICS_AND_DEMO_SCENARIOS.md) —
  equations, numerical assumptions, and scenario background.
- [Lunar landing roadmap](./LUNAR_LANDING_ROADMAP.md) — what would be needed
  to progress toward a realistic touchdown simulation.
- [Lunar Demo preset](../presets/spacecraft/lunar_demo.json) — the editable
   spacecraft definition.
- [Apollo 11 source and data notes](../LUNAR_DATA.md) — provenance for the
  fixed historical reference and documented data gaps.
