"""OpenGL scene for the spacecraft configurator: vehicle, grid, selection, camera."""
import numpy as np

from spacecraft.geometry import (
    FLAG_COLORS,
    FLAG_GRIDS,
    layout_spacecraft,
    primitive,
    scale,
    translate,
)

from .flight import LANDED, FlightAnimation
from .orbit_camera import OrbitCamera

MOON_COLOR = (1.0, 1.0, 1.0)
FLAME_COLOR = (1.0, 0.8, 0.35)
FLASH_COLOR = (1.0, 0.65, 0.2)
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
        self.flight = FlightAnimation()
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

    # -- mission flight animation ---------------------------------------------

    def start_flight(self, liftoff: bool = True, has_thrust: bool = True) -> None:
        """Start the mission; the outcome is applied later by finish_flight.

        With ``liftoff=False`` the vehicle strains on the pad and never leaves it.
        """
        self._refresh_layout()
        self.flight.launch(
            self.layout.center,
            self.layout.height,
            self.layout.core_radius,
            liftoff=liftoff,
            has_thrust=has_thrust,
        )

    def finish_flight(self, outcome: str) -> None:
        """Mission verdict: land on the Moon, fly past it, or fall back down."""
        self.flight.conclude(outcome)

    def reset_flight(self) -> None:
        if self.flight.active:
            self.flight.reset()
            self.invalidate(reframe=True)

    def update(self, dt: float) -> None:
        """Advance the flight animation and keep the camera on it."""
        if not self.flight.active:
            return
        self.flight.update(dt)
        centre, radius = self.flight.focus()
        self.camera.follow(centre, radius, dt)

    def _refresh_layout(self) -> None:
        if not self._dirty:
            return
        self.layout = layout_spacecraft(self.get_spacecraft(), self.explode)
        if self._reframe:
            self.camera.frame(self.layout.camera_center, self.layout.bounding_radius)
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
            if self.flight.active:
                span = max(span, 8.0 * self.flight.height)
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
        flight = self.flight
        flying = flight.active
        ids = {cid: index + 1 for index, cid in enumerate(self.layout.component_ids())}
        if not flying:
            for cid, pick in ids.items():
                self._pick_ids[pick] = cid
        world = flight.vehicle_matrix() if flying else None
        for part in self.layout.parts:
            if flying and not flight.vehicle_visible:
                break
            highlight = 0.0
            if part.component_id is not None:
                if part.component_id == self.selected_id:
                    highlight = 1.0
                elif part.component_id == self.hovered_id:
                    highlight = 0.35
            renderer.draw_mesh(
                part.primitive,
                primitive(part.primitive),
                part.model if world is None else world @ part.model,
                part.color,
                highlight=highlight,
                pick_id=0 if flying else ids.get(part.component_id, 0),
            )
        if flying:
            self._render_flight(renderer, world)

    def _render_flight(self, renderer, world) -> None:
        flight = self.flight
        if flight.moon_visible:
            renderer.draw_mesh(
                "sphere",
                primitive("sphere"),
                translate(*flight.moon_center) @ scale(*(3 * [flight.moon_radius])),
                MOON_COLOR,
            )
        if flight.state == LANDED:
            self._render_landed_flag(renderer)
        if flight.burning and flight.vehicle_visible:
            radius = 0.7 * flight.core_radius
            # The nose primitive points +Y; a negative Y scale makes it a plume below the base.
            renderer.draw_mesh(
                "nose",
                primitive("nose"),
                world @ scale(radius, -flight.flame_length(), radius),
                FLAME_COLOR,
                highlight=0.8,
            )
        flash = flight.flash()
        if flash is not None:
            centre, radius, fade = flash
            renderer.draw_mesh(
                "sphere",
                primitive("sphere"),
                translate(*centre) @ scale(radius, radius, radius),
                tuple(c * (0.35 + 0.65 * fade) for c in FLASH_COLOR),
                highlight=fade,
            )

    def _render_landed_flag(self, renderer) -> None:
        appearance = self.get_spacecraft().appearance
        flag_grid = FLAG_GRIDS.get(appearance.national_flag)
        if flag_grid is None:
            return

        flight = self.flight
        up = flight.landing_normal / np.linalg.norm(flight.landing_normal)
        side = np.cross(up, np.array((0.0, 1.0, 0.0)))
        if np.linalg.norm(side) < 1e-6:
            side = np.cross(up, np.array((0.0, 0.0, 1.0)))
        side /= np.linalg.norm(side)
        ground_normal = up * flight.moon_radius + side * (1.25 * flight.height)
        ground_normal /= np.linalg.norm(ground_normal)
        base = flight.moon_center + ground_normal * flight.moon_radius

        toward_camera = self.camera.eye.astype(np.float64) - base
        toward_camera -= np.dot(toward_camera, ground_normal) * ground_normal
        if np.linalg.norm(toward_camera) < 1e-6:
            toward_camera = side
        toward_camera /= np.linalg.norm(toward_camera)
        right = np.cross(ground_normal, toward_camera)
        right /= np.linalg.norm(right)
        front = np.cross(right, ground_normal)
        frame = np.eye(4, dtype=np.float32)
        frame[:3, :3] = np.column_stack((right, ground_normal, front))

        pole_height = 1.55 * flight.height
        renderer.draw_mesh(
            "cylinder",
            primitive("cylinder"),
            translate(*base)
            @ frame
            @ scale(
                0.025 * flight.height,
                pole_height,
                0.025 * flight.height,
            ),
            (0.72, 0.76, 0.82),
        )

        flag_width = 0.95 * flight.height
        flag_height = flag_width * 5.0 / 7.0
        tile_width = flag_width / 7.0
        tile_height = flag_height / 5.0
        flag_frame = (
            translate(*base)
            @ frame
            @ translate(0.52 * flight.height, 1.15 * flight.height, 0.0)
        )
        renderer.draw_mesh(
            "box",
            primitive("box"),
            flag_frame
            @ scale(
                flag_width * 1.08,
                flag_height * 1.12,
                0.025 * flight.height,
            ),
            (0.08, 0.10, 0.14),
        )
        for row, pattern in enumerate(flag_grid):
            for column, symbol in enumerate(pattern):
                renderer.draw_mesh(
                    "box",
                    primitive("box"),
                    flag_frame
                    @ translate(
                        (column - 3) * tile_width,
                        (2 - row) * tile_height,
                        0.015 * flight.height,
                    )
                    @ scale(
                        tile_width * 1.02,
                        tile_height * 1.02,
                        0.009 * flight.height,
                    ),
                    FLAG_COLORS[symbol],
                )

    def pick(self, renderer, x: float, y: float) -> str | None:
        """Return the component id under normalized coords, or None."""
        return self._pick_ids.get(renderer.pick(x, y))


__all__ = ["SpacecraftViewport", "grid_lines"]
