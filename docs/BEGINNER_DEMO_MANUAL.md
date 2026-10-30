# Celeste SpaceWorks

## Overview

Celeste SpaceWorks is an interactive spacecraft mission-design and analysis platform that combines spacecraft assembly, engineering evaluation, 3D visualization, and Earth-to-Moon mission screening in a single workflow.

Users can:

- Assemble spacecraft from modular subsystems.
- Visualize spacecraft architecture in an interactive 3D environment.
- Explore how mass, propulsion, power, and vehicle layout affect performance.
- Evaluate engineering metrics such as thrust-to-weight ratio, delta-v, power balance, and stability.
- Test whether a vehicle can satisfy the requirements of a modeled Earth-to-Moon mission.
- Understand why a mission succeeds or fails through engineering and mission-analysis feedback.

The goal is not to produce a flight-certified spacecraft. The goal is to help users explore spacecraft-design tradeoffs and understand how engineering decisions influence mission outcomes.

---

## What Makes This Project Different?

Spacecraft design and mission analysis are often treated as separate activities.

This project connects them.

A user can:

1. Build a spacecraft.
2. Analyze its engineering characteristics.
3. Visualize the vehicle architecture.
4. Evaluate a lunar mission.
5. Understand the reasons behind mission success or failure.

The platform combines vehicle design, analysis, and mission evaluation in a single experience.

---

## Real Data Used by the Platform

The platform incorporates real-world aerospace reference and astronomy data, including:

### Historical Mission References

- Apollo 11 launch profile
- Kennedy Space Center Launch Complex 39A
- NASA mission reference data

### Astronomical Data

- JPL DE440 ephemerides
- Date-specific Earth-Moon geometry
- Date-specific Moon and Sun positions

### Orbital Mechanics

- Lambert transfer calculations
- Numerical trajectory propagation
- Earth-to-Moon transfer analysis
- Lunar sphere-of-influence evaluation

### Vehicle Models

Spacecraft components use representative engineering models to allow rapid exploration of mission-design tradeoffs.

The focus is engineering understanding rather than reproducing specific flight hardware.

---

## What the Platform Evaluates

The software helps answer questions such as:

- How much does the spacecraft weigh?
- Does the available thrust exceed vehicle weight?
- Is the available propellant compatible with the engine?
- How much ideal delta-v is available?
- Is the power system balanced?
- Is the vehicle geometrically stable?
- Can the design satisfy the requirements of a modeled lunar mission?
- If not, what constraint prevents mission success?

---

## What a Successful Mission Means

A successful mission result indicates that:

- The spacecraft passes the configured vehicle checks.
- The available delta-v satisfies modeled mission requirements.
- The propagated trajectory enters the Moon's estimated sphere of influence.

A successful result does **not** establish:

- Launch readiness
- Flight certification
- Lunar orbit insertion
- Lunar capture
- Safe landing
- Operational mission success

Mission results should be interpreted as engineering-screening outcomes rather than flight validation.

---

## Suggested Demo Narrative

### Problem

Spacecraft design, mission planning, and engineering analysis are typically performed using separate tools. This makes it difficult to understand how design choices affect mission feasibility.

### Solution

Spacecraft Configurator combines vehicle design, engineering analysis, and lunar mission evaluation in a single interactive platform.

### Demo

#### 1. Design

Build or load a spacecraft and show the 3D vehicle.

Highlight:

- Engines
- Tanks
- Payload
- Power systems
- Landing systems

#### 2. Analyze

Show:

- Mass
- Delta-v
- Thrust-to-weight ratio
- Power balance
- Stability metrics

Demonstrate how modifying a component changes the vehicle's engineering characteristics.

#### 3. Validate

Run a mission simulation.

Show:

- Date-specific Earth-Moon geometry
- Mission timeline
- Mission screening results
- Failure or success explanations

#### 4. Compare Outcomes

Run a successful lunar encounter scenario.

Then load a failure scenario and show how a single design constraint can prevent mission success.

---

## One-Sentence Project Description

Spacecraft Configurator is an interactive spacecraft mission-design platform that enables users to assemble vehicles, evaluate engineering tradeoffs, visualize spacecraft architecture, and analyze Earth-to-Moon mission feasibility using real astronomical data and historical mission references.
