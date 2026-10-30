"""OpenGL scene for the spacecraft configurator: vehicle, grid, selection, camera."""
import numpy as np

from spacecraft.geometry import layout_spacecraft, primitive

from .orbit_camera import OrbitCamera

GRID_COLOR = (0.30, 0.34, 0.42, 0.55)
AXIS_COLORS = {
    "x": (0.85, 0.25, 0.25, 0.9),
    "z": (0.30, 0.45, 0.90, 0.9),
}


def grid_lines(half_extent: float, step: float) -> np.ndarray:
    """Ground-plane grid segment endpoints as an (N*2, 3) array."""
    count = int(half_extent // step)
    ticks = np.arange(-count, count + 1) * step
    lines = []
    for t in ticks:
        lines.append(((t, 0.0, -half_extent), (t, 0.0, half_extent)))
        lines.append(((-half_extent, 0.0, t), (half_extent, 0.0, t)))
    return np.array(lines, dtype=np.float32).reshape(-1, 3)


class SpacecraftViewport:
    """Owns the camera and draws a spacecraft layout into an OpenGLRenderer.

    The designer UI is the source of truth for the spacecraft; this class only
    reads it through ``get_spacecraft`` and reports selection via callbacks.
    """

    def __init__(self, get_spacecraft):
        self.get_spacecraft = get_spacecraft
        self.camera = OrbitCamera()
        self.layout = layout_spacecraft(None)
        self.selected_id: str | None = None
        self.hovered_id: str | None = None
        self.explode = 0.0
        self.show_grid = True
        self._dirty = True
        self._reframe = True
        self._pick_ids: dict[int, str | None] = {}

    def invalidate(self, reframe: bool = False) -> None:
        self._dirty = True
        self._reframe = self._reframe or reframe

    def reset_camera(self) -> None:
        self.camera = OrbitCamera()
        self._dirty = True
        self._reframe = True

    def _refresh_layout(self) -> None:
        if not self._dirty:
            return
        self.layout = layout_spacecraft(self.get_spacecraft(), self.explode)
        if self._reframe:
            self.camera.frame(self.layout.center, self.layout.bounding_radius)
            self._reframe = False
        else:
            self.camera.min_distance = max(0.2, self.layout.bounding_radius * 0.25)
            self.camera.max_distance = max(50.0, self.layout.bounding_radius * 20.0)
        self._dirty = False

    def render(self, renderer) -> None:
        self._refresh_layout()
        renderer.set_camera(
            self.camera.view_projection(renderer.aspect),
            self.camera.eye,
        )

        if self.show_grid:
            span = max(20.0, self.layout.bounding_radius * 3.0)
            step = 1.0 if span <= 40.0 else 5.0
            half = np.ceil(span / step) * step
            renderer.draw_lines_3d(grid_lines(half, step), GRID_COLOR)
            renderer.draw_lines_3d(
                np.array([(-half, 0, 0), (half, 0, 0)], dtype=np.float32),
                AXIS_COLORS["x"],
            )
            renderer.draw_lines_3d(
                np.array([(0, 0, -half), (0, 0, half)], dtype=np.float32),
                AXIS_COLORS["z"],
            )

        self._pick_ids = {}
        ids = {cid: index + 1 for index, cid in enumerate(self.layout.component_ids())}
        for cid, pick in ids.items():
            self._pick_ids[pick] = cid
        for part in self.layout.parts:
            highlight = 0.0
            if part.component_id is not None:
                if part.component_id == self.selected_id:
                    highlight = 1.0
                elif part.component_id == self.hovered_id:
                    highlight = 0.35
            renderer.draw_mesh(
                part.primitive,
                primitive(part.primitive),
                part.model,
                part.color,
                highlight=highlight,
                pick_id=ids.get(part.component_id, 0),
            )

    def pick(self, renderer, x: float, y: float) -> str | None:
        """Return the component id under normalized coords, or None."""
        return self._pick_ids.get(renderer.pick(x, y))


__all__ = ["SpacecraftViewport", "grid_lines"]

