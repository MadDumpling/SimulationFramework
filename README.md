# Taichi Simulation Template

A reusable Python template for building interactive simulations with Taichi.

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
├── run.sh
├── test.sh
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
- Python 3.12

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
