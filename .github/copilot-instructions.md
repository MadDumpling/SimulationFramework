# Copilot Instructions

## Project Guidelines
- Prefer phased renderer migration: move from Taichi Window canvas rendering to DearPyGui viewport via dynamic texture, introduce render(renderer, camera) abstraction before removing ti.ui.Window.