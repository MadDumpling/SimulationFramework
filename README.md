# Taichi Simulation Template

A reusable Python template for building interactive simulations with Taichi. The goal is to decrease the time spent on infrastructure for building CAD or simulation software. 

## Features

- Taichi GPU simulation engine
- DearPyGui control panel
- Editable simulation parameters
- Pause / Resume / Reset controls
- JSON configuration presets
- Screenshot and recording support
- Pytest testing setup
- Modular architecture for rapid prototyping

## Project Structure

```text
.
├── app.py                 # Main application entrypoint
├── simulation.py          # Base simulation logic
├── requirements.txt
├── pyproject.toml
├── setup.sh
├── setup.ps1
├── run.sh
├── run.ps1
├── test.sh
├── test.ps1
├── presets/
│   └── default.json
├── recordings/
└── tests/
    └── test_simulation.py
```

## Quick Start

## Supported Python Versions

This project currently supports:

- Python 3.11

Python 3.14+ is not currently supported by Taichi.
### Clone the repository

```bash
git clone <repo-url>
cd sim-template
```

### Setup

```bash
chmod +x setup.sh
./setup.sh
```

Windows PowerShell:

```powershell
.\setup.ps1
```

### Activate Environment

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## Visual Studio Setup (Windows)

### Prerequisites

Install:

- Python 3.11+
- Visual Studio with Python Development workload
- Git (optional)

Verify Python is installed:

```powershell
python --version
```

or

```powershell
py --version
```

---

### Create a Virtual Environment

Open a terminal in the project root:

```powershell
python -m venv .venv
```

If that fails:

```powershell
py -m venv .venv
```

This creates a local virtual environment in:

```text
.venv/
```

---

### Activate the Virtual Environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

You should now see:

```text
(.venv) PS C:\...\SimulationHackathonFramework>
```

---

### Install Dependencies

```powershell
python -m pip install --upgrade pip

pip install -r requirements.txt
```

---

### Configure Visual Studio

1. Open the project folder.
2. Open **Python Environments**.
3. Select the `.venv` environment.
4. Set `app.py` as the startup file.

---

### Running the Application

From Visual Studio:

- Press **F5** to run with debugging.
- Press **Ctrl + F5** to run without debugging.

Or from the terminal:

```powershell
python app.py
```

Windows PowerShell:

```powershell
.\run.ps1
```

---

### Running Tests

Run all tests:

```powershell
pytest
```

Verbose output:

```powershell
pytest -v
```

Windows PowerShell:

```powershell
.\test.ps1
```

Coverage:

```powershell
pytest --cov
```

---

### Common Issues

#### PowerShell Execution Policy

If activation fails with an execution policy error:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

#### Virtual Environment Not Found

Make sure you have created it first:

```powershell
python -m venv .venv
```

#### Requirements Installation Fails

Upgrade pip and retry:

```powershell
python -m pip install --upgrade pip

pip install -r requirements.txt
```

---

### Verify Installation

Run:

```powershell
python -c "import taichi as ti; print(ti.__version__)"
```

Expected output:

```text
1.x.x
```

If a version number is displayed, Taichi is installed correctly.

The application attempts to use the GPU first and automatically falls back to
the CPU when a compatible GPU backend is unavailable.

### Run

```bash
./run.sh
```

or

```bash
python app.py
```

## Testing

Run all tests:

```bash
./test.sh
```

or

```bash
pytest -v
```

Generate coverage:

```bash
pytest --cov
```

## Creating a New Simulation

### 1. Create a Simulation Class

Inside `simulations/` create a new file:

```text
simulations/
└── my_simulation.py
```

Example:

```python
from simulations.base import Simulation

class MySimulation(Simulation):
    pass
```

---

### 2. Define Editable Parameters

Create parameters inside `__init__`:

```python
from parameters import Parameter

self.parameters = {
    "speed": Parameter(
        "Speed",
        10.0,
        0.0,
        50.0,
    ),
    "radius": Parameter(
        "Radius",
        0.01,
        0.001,
        0.05,
    ),
}
```

Each parameter automatically generates a UI slider.

---

### 3. Use Parameters in Simulation Logic

Access parameter values through:

```python
speed = self.parameters["speed"].value
radius = self.parameters["radius"].value
```

Example:

```python
def step(self):
    speed = self.parameters["speed"].value

    self._step(speed)
```

---

### 4. Implement Required Methods

```python
def reset(self):
    pass

def step(self):
    pass

def render(self, canvas):
    pass
```

---

### 5. Register the Simulation

Edit:

```python
simulations/__init__.py
```

```python
from .my_simulation import MySimulation
```

---

### 6. Launch It

In `app.py`:

```python
simulation = MySimulation()
```

The UI will automatically display all parameters defined in:

```python
self.parameters
```
## Configuration

Simulation presets live in:

```text
presets/
```

Example:

```json
{
    "gravity": 9.81,
    "dt": 0.01,
    "particle_count": 1000
}
```

## Recommended Workflow

1. Build simulation kernel
2. Expose parameters in UI
3. Add presets
4. Add recording/export
5. Create demo scenario
6. Prepare final presentation

## Dependencies

Core libraries:

- taichi
- dearpygui
- numpy
- pandas
- pyyaml
- matplotlib
- imageio
- pytest

## Hackathon Tips

- Keep parameters configurable.
- Build recording support early.
- Always have a stable demo preset.
- Track FPS and simulation statistics.
- Favor reliability over complexity.

# Framework Progress

## Version 0.1 - Initial Framework

### Completed Features

#### Simulation Architecture

Moved simulation logic out of `app.py`.

Before:

```text
app.py
 ├─ physics
 ├─ rendering
 ├─ ui
 └─ window
```

After:

```text
app.py
 ├─ application lifecycle
 ├─ main loop
 └─ simulation orchestration

simulations/
 └─ bouncing_balls.py
```

Benefits:

- Simulations are isolated
- Easy to add new simulations
- Cleaner project structure

---

#### Simulation Package

Added:

```text
simulations/
├── __init__.py
├── base.py
└── bouncing_balls.py
```

Purpose:

- Encapsulate simulation implementations
- Support multiple simulation types

Future:

```text
boids.py
fluid.py
cloth.py
reaction_diffusion.py
```

---

#### UI Package

Added:

```text
ui/
├── __init__.py
└── controls.py
```

Purpose:

- Separate UI from simulation logic
- Centralized framework controls

Current Controls:

- Pause
- Reset

Future Controls:

- FPS counter
- Screenshot
- Recording
- Simulation selector

---

#### Parameter System

Added:

```python
class Parameter
```

in:

```text
parameters.py
```

Purpose:

- Define editable simulation values
- Automatically generate UI controls

Example:

```python
Parameter(
    "Gravity",
    9.8,
    0.0,
    20.0,
)
```

---

#### Automatic Parameter UI

Parameters are stored in:

```python
self.parameters
```

Example:

```python
self.parameters = {
    "gravity": Parameter(...),
    "radius": Parameter(...),
    "damping": Parameter(...),
}
```

The UI automatically creates sliders for all parameters:

```python
for parameter in simulation.parameters.values():
```

No UI changes are required when adding new parameters.

Benefits:

- Rapid iteration
- Reusable framework
- Less duplicated code

---

#### Parameter-Driven Simulation

Removed hardcoded values:

Before:

```python
9.8
0.9
0.01
```

After:

```python
self.parameters["gravity"].value
self.parameters["damping"].value
self.parameters["radius"].value
```

Benefits:

- Runtime editing
- Better experimentation
- Hackathon-friendly workflow

---

#### Bouncing Balls Demo

Implemented:

- Particle initialization
- Gravity
- Ground collision
- Damping
- Runtime parameter editing

Purpose:

- Validate framework architecture
- Test UI integration
- Test Taichi rendering pipeline

---

## Current Architecture

```text
SimulationHackathonFramework/
│
├── app.py
├── parameters.py
│
├── simulations/
│   ├── __init__.py
│   ├── base.py
│   └── bouncing_balls.py
│
├── ui/
│   ├── __init__.py
│   └── controls.py
│
├── tests/
│
├── requirements.txt
├── README.md
└── pyproject.toml
```

---
# Framework Progress

## Version 0.2 - Plugin Architecture Foundation

This milestone transitions the project from a single hardcoded simulation into a simulation framework capable of discovering and managing simulations dynamically.

---

# Completed Features

## Simulation Architecture

Simulation logic has been fully separated from application lifecycle management.

### Application Responsibilities

```text
app.py
├── Taichi initialization
├── Window management
├── Main loop
├── Input processing
├── Simulation orchestration
└── UI orchestration
```

### Simulation Responsibilities

```text
simulations/
├── base.py
└── bouncing_balls.py
```

### Benefits

- Clear separation of concerns
- Easier maintenance
- New simulations can be added independently
- Foundation for plugins and scripting

---

## Base Simulation Interface

All simulations inherit from:

```python
class Simulation(ABC):
```

Required methods:

```python
reset()
step()
render(canvas, camera)
```

Metadata support:

```python
name
author
version
```

Example:

```python
class BouncingBalls(Simulation):
    name = "Bouncing Balls"
    author = "You"
    version = "0.1"
```

### Benefits

- Standardized simulation contract
- Consistent behavior across simulations
- Automatic registration support

---

## Parameter System

Framework-level parameter abstraction:

```python
class Parameter:
```

Example:

```python
Parameter(
    "Gravity",
    9.8,
    0.0,
    20.0
)
```

Current usage:

```python
self.parameters = {
    "gravity": Parameter(...),
    "damping": Parameter(...),
    "radius": Parameter(...),
}
```

### Benefits

- Runtime editing
- UI auto-generation
- Future preset serialization
- Future scripting support

---

## Automatic Parameter UI

UI controls are generated automatically.

Example:

```python
for parameter in simulation.parameters.values():
```

The framework creates:

```text
Gravity Slider
Damping Slider
Radius Slider
```

without requiring custom UI code.

### Benefits

- Rapid development
- Minimal boilerplate
- Scales to future simulations

---

## Simulation Registry

Added:

```text
registry.py
```

### Purpose

- Central storage of available simulations
- Automatic simulation discovery
- Dynamic instantiation

Registry structure:

```python
SIMULATIONS = {}
```

Example registration:

```python
@register_simulation
class BouncingBalls(Simulation):
    ...
```

Result:

```python
SIMULATIONS = {
    "Bouncing Balls": BouncingBalls
}
```

### Benefits

- No hardcoded simulation lists
- Dynamic framework discovery
- Required for plugins and hot reloading

---

## Plugin Loader

Added:

```text
plugin_loader.py
```

### Purpose

- Discover simulations automatically
- Import simulation modules dynamically
- Populate the simulation registry

Example:

```python
load_simulations()
```

Loader scans:

```text
simulations/
├── bouncing_balls.py
├── boids.py
├── fluid.py
└── cloth.py
```

Every discovered simulation is automatically registered.

### Benefits

- Zero manual registration
- Plugin architecture foundation
- Future drop-in simulation support

---

## Plugin-Based Simulation Creation

Simulations can now be created through the registry.

Example:

```python
simulation = SIMULATIONS[
    "Bouncing Balls"
]()
```

Future:

```python
simulation = create_simulation(
    "Boids"
)
```

### Benefits

- Dynamic simulation switching
- No direct imports required
- Supports UI-driven selection

---

## Bouncing Balls Demo

Current reference simulation.

### Implemented

- Particle initialization
- Gravity
- Ground collision
- Damping
- Camera support
- Runtime parameter editing

### Purpose

- Validate architecture
- Validate registry system
- Validate plugin loading
- Validate parameter framework

---

## Testing Infrastructure

Added:

```text
tests/
```

Framework now includes automated tests.

### Registry

```text
✓ Simulation registration
✓ Registry population
```

### Plugin Loading

```text
✓ Dynamic discovery
✓ Import loading
```

### Parameters

```text
✓ Parameter creation
✓ Parameter storage
```

### Simulation Metadata

```text
✓ Name
✓ Author
✓ Version
```

### Simulation Creation

```text
✓ Registry-based instantiation
```

### UI Controls

```text
✓ Control state management
✓ Pause functionality
```

### Current Status

```text
10/10 tests passing
```

---

# Current Architecture

```text
SimulationHackathonFramework/
│
├── app.py
├── registry.py
├── plugin_loader.py
├── parameters.py
│
├── simulations/
│   ├── __init__.py
│
```

# Version 0.3 - Application Architecture & Editor Foundation

This milestone transforms the framework from a collection of interconnected systems into a structured application architecture with clear ownership boundaries, rendering abstraction, and event-driven communication.

---

# Major Architectural Refactor

## Previous Architecture (v0.2)

```text
app.py
│
├── Taichi Initialization
├── Plugin Loading
├── SimulationManager
├── InputManager
├── SimulationUI
├── Window Creation
├── Main Loop
└── DearPyGui Lifecycle
```

`app.py` acted as the application's God Object and contained responsibilities from every subsystem.

---

## New Architecture (v0.3)

```text
app.py
│
├── Application
│     └── DearPyGui Lifecycle
│
└── SimulationApplication
      │
      ├── EventBus
      ├── SimulationManager
      ├── SimulationUI
      ├── InputManager
      └── TaichiRenderer
```

### Benefits

- Clear ownership boundaries
- Better separation of concerns
- Easier testing
- Reduced coupling
- Foundation for editor-style workflow
- Enables future plugin ecosystem

---

# Application Lifecycle System

Added:

```text
ui/
└── application.py
```

```python
class Application:
```

### Responsibilities

- DearPyGui Context Creation
- Viewport Creation
- Frame Rendering
- Application Shutdown

### Example

```python
app = Application()

app.initialize()

while app.running():

    app.render()

app.shutdown()
```

### Benefits

- UI lifecycle isolated
- No DPG management in feature code
- Easier future editor integration

---

# Simulation Application Layer

Added:

```text
ui/
└── simulation_application.py
```

```python
class SimulationApplication:
```

### Responsibilities

- Simulation Orchestration
- Input Handling
- Simulation Updates
- Renderer Coordination
- UI Coordination

### Example

```python
simulation_app = (
    SimulationApplication()
)

simulation_app.initialize()

simulation_app.update()

simulation_app.render()
```

### Benefits

- Application behavior centralized
- Cleaner startup process
- Easier future extension

---

# Renderer Abstraction

Added:

```text
rendering/
├── __init__.py
└── taichi_renderer.py
```

```python
class TaichiRenderer:
```

### Responsibilities

- Window Creation
- Canvas Management
- Frame Lifecycle
- Simulation Rendering
- Presentation

### Example

```python
renderer.begin_frame()

renderer.render(
    simulation,
    camera,
)

renderer.end_frame()
```

### Benefits

- Rendering backend isolated
- Future OpenGL/Vulkan support possible
- Future embedded viewport support
- Reduced coupling to Taichi

---

# Event System

Added:

```text
core/
├── __init__.py
└── event_bus.py
```

```python
class EventBus:
```

### Supports

```python
publish()
subscribe()
```

### Example

```python
events.publish(
    "simulation.load",
    "Boids",
)
```

```python
events.subscribe(
    "simulation.load",
    manager.load,
)
```

### Benefits

- Event-driven architecture
- Reduced component coupling
- Foundation for plugins
- Foundation for scripting
- Foundation for console commands
- Foundation for networking

---

# UI Refactor

SimulationUI now communicates through events.

### Previous

```python
self.manager.load(
    simulation_name
)
```

### Current

```python
self.events.publish(
    "simulation.load",
    simulation_name,
)
```

### Previous

```python
self.manager.reset()
```

### Current

```python
self.events.publish(
    "simulation.reset"
)
```

### Benefits

- UI no longer directly controls systems
- Cleaner architecture
- Extensible communication pipeline

---

# Main Loop Refactor

### Previous

```python
input_manager.update(...)

manager.step()

manager.render(...)

ui.render()
```

### Current

```python
simulation_app.update()

simulation_app.render()

app.render()
```

### Benefits

- Higher-level orchestration
- Cleaner startup file
- Clear subsystem ownership

---

# App.py Simplification

The application entry point has been reduced to orchestration only.

### Current Responsibilities

- Taichi Initialization
- Plugin Discovery
- Application Startup
- Main Loop
- Shutdown

### No Longer Responsible For

- Window Management
- Rendering
- Simulation Coordination
- Input Handling
- UI Lifecycle

---

# Current Folder Structure

```text
SimulationHackathonFramework/
│
├── app.py
│
├── core/
│   ├── __init__.py
│   └── event_bus.py
│
├── rendering/
│   ├── __init__.py
│   └── taichi_renderer.py
│
├── ui/
│   ├── __init__.py
│   ├── application.py
│   ├── controls.py
│   ├── layout.py
│   └── simulation_application.py
│
├── simulations/
│   ├── __init__.py
│   ├── base.py
│   └── bouncing_balls.py
│
├── simulation_manager.py
├── plugin_loader.py
├── registry.py
├── parameters.py
└── app.py
```

---

# Design Goals Achieved

## Separation of Concerns

```text
Application
↓
UI Lifecycle
```

```text
SimulationApplication
↓
Simulation Coordination
```

```text
TaichiRenderer
↓
Rendering
```

```text
SimulationManager
↓
Simulation State
```

---

## Reduced Coupling

### Previous

```text
SimulationUI
    ↓
SimulationManager
```

### Current

```text
SimulationUI
      ↓
   EventBus
      ↓
SimulationManager
```

---

## Editor Foundation

The framework is now structured more like a simulation editor than a standalone demo application.

Future systems can connect through events:

```text
Console
Keyboard Shortcuts
Plugins
Replay System
Timeline
Python Scripts
Networking
Node Editor
```

---

# Current Status

## Implemented

✅ Application Lifecycle Layer

✅ Simulation Application Layer

✅ Renderer Abstraction

✅ Event Bus System

✅ Reduced Coupling

✅ Cleaner Main Loop

✅ Editor-Oriented Architecture

✅ Dynamic Plugin Loading

✅ Parameter System

✅ Auto-Generated UI Controls

✅ Runtime Simulation Switching

✅ Bouncing Balls Reference Simulation

---

# Testing Status

Framework architecture remains compatible with:

```text
✓ Simulation Registration
✓ Plugin Discovery
✓ Simulation Creation
✓ Parameters
✓ Metadata
✓ UI Controls
✓ Simulation Manager
```

Target:

```text
10/10 Tests Passing
```

---

# Roadmap

## v0.3.x

### Framework

- FPS Display
- Logging System
- Console Window
- Event Constants
- Keyboard Shortcuts
- Preset Serialization
- Save/Load Parameters

### Simulations

- Boids
- Particle Life
- Reaction Diffusion

---

## v0.4

### Tooling

- Replay System
- Timeline Scrubber
- Recording
- Screenshots
- Session Serialization

---

## v0.5

### Extensibility

- Embedded Python Runtime
- Hot Reloading (watchdog)
- API Introspection
- Script Templates

---

## v1.0

### Editor Features

- Integrated Documentation
- Node Editor
- Drag-and-Drop Simulation Graph
- Embedded Simulation Viewport
- Complete Plugin Ecosystem

---

# Summary

Version **0.3** introduces the framework's first true application architecture.

The project has evolved from a simulation demo into a modular simulation framework with a clear separation between:

- Application Lifecycle
- Rendering
- Simulation Management
- User Interface
- Event Communication

The framework is now positioned for advanced editor-style tooling, scripting, replay systems, hot reloading, and a full plugin ecosystem.


### Quality

- [ ] Additional tests
- [ ] Configuration presets
- [ ] Save/load parameter profiles
