For a hackathon, I'd write something like this in your roadmap/design document.

UX & Visualization Roadmap
Goal

The configurator should feel like designing a spacecraft, not filling out a form.

Users must be able to:

Add components.
Select components directly in the 3D viewport.
Modify component placement visually.
Understand vehicle mass distribution and stability.
See why a mission succeeds or fails.

The emphasis is usability and visual feedback rather than CAD-level accuracy.

V1: Interactive Part Selection
Requirements
Every visible component is selectable.
Clicking a part in the viewport highlights it.
The selected part is also highlighted in the component list.
The component inspector updates automatically.
Visual Behavior

Selected component:

Orange outline or highlight.
Slight brightness increase.
Name shown in inspector.

The existing picking system should be used:

renderer.pick(x, y)


No additional selection system is required.

V2: Component Inspector
Goal

Allow direct editing of a selected component.

Inspector Fields

For all components:

Name
Mass
Stage
Position
Rotation


For engines:

Thrust
Specific Impulse
Throttle Range


For tanks:

Capacity
Current Propellant
Residual Propellant


Changes update immediately in the viewport.

V3: Manual Placement
Goal

Replace automatic placement with user-controlled placement.

Placement Data

Each component may define:

placement:
    parent_id
    parent_node
    node
    offset
    rotation

User Experience

Example:

Add Fuel Tank


Tank appears.

User selects:

Position X
Position Y
Position Z


Changes are reflected immediately.

No restart or reload required.

V4: Attachment System
Goal

Allow spacecraft assembly from connected parts.

Supported Nodes
TOP
BOTTOM
SIDE
MOUNT

Workflow

Example:

Select Engine

Attach To:
Main Fuel Tank

Parent Node:
Bottom


Engine snaps to the tank.

This is similar to:

Kerbal Space Program
Space Engineers
Orbiter
V5: Symmetry Placement
Goal

Speed up repetitive design tasks.

Supported Modes
Off
2x
3x
4x
6x
8x

Example

Adding one landing leg:

Symmetry = 4


Creates:

Leg 1
Leg 2
Leg 3
Leg 4


around the vehicle.

Useful for:

Landing legs
RCS thrusters
Engine clusters
Solar arrays
V6: Center of Mass Visualization
Goal

Help users understand balance and stability.

Display

Render:

Yellow sphere


at vehicle center of mass.

Use:

mass_properties()


already available in the codebase.

Additional Information

Display:

Vehicle Mass
Center of Mass
Tip-over Angle


in analysis panel.

V7: Stability Visualization
Goal

Help users understand landing behavior.

Display

Show:

Landing Footprint


using landing gear radius.

Render:

Green circle


under vehicle.

Show:

Tip-over limit


using:

static_tip_over_angle_deg()


Warnings:

UNSTABLE LANDER
Center of mass outside safe region

V8: Mission Outcome Visualization
Goal

Clearly communicate simulation results.

Replace the current binary success/failure display.

Mission States
READY
SIMULATING
FAILED
SAFE LANDING

Flight Events

Display timeline:

✓ Launch

✓ Earth Orbit

✓ Translunar Injection

✓ Lunar Arrival

✗ Touchdown
Hard Landing


or

✓ Launch

✓ Earth Orbit

✓ Translunar Injection

✓ Lunar Arrival

✓ Safe Landing

V9: Apollo LM Showcase
Demo Mode

Provide:

Load Apollo Lunar Module


button.

Displays:

Apollo LM
NASA-derived reference vehicle


Shows:

Mass
Engine
Landing gear
Apollo 11 landing site

This should be the primary hackathon demonstration vehicle.

Non-Goals for Hackathon

The following are explicitly out of scope:

Full CAD editing
Real-time mesh modelling
Finite-element analysis
Full 6-DOF flight controls
Detailed propellant slosh simulation
GRAIL high-order gravity visualization
Perfect Apollo telemetry reconstruction

The objective is an intuitive spacecraft design and mission-planning experience, not an engineering certification tool.

Hackathon MVP

If time is limited, implement only:

Part selection.
Position editing.
Attachment nodes.
Center-of-mass visualization.
Apollo LM preset.
Improved mission-state display.

Those six features will provide the highest visible impact for judges and users.
