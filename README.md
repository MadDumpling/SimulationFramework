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

Extend the base Simulation class:

```python
class Simulation:
    def __init__(self):
        pass

    def step(self):
        pass

    def render(self):
        pass

    def reset(self):
        pass
```

Implement your simulation logic inside:

- `step()` for physics updates
- `render()` for visualization
- `reset()` for initialization

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
