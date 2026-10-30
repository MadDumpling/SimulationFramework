# Copilot Instructions

## Project Guidelines
- The app is a spacecraft configurator: the DearPyGui designer panel edits a `Spacecraft`, and `viewport.SpacecraftViewport` draws it with the offscreen OpenGL renderer into a DearPyGui dynamic texture.
- Keep `spacecraft/` (domain, geometry) free of UI and GL imports so it stays testable headlessly.
