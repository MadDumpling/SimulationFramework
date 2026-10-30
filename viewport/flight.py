"""Visual flight animation for the mission button.

This illustrates the outcome; it is not a trajectory simulation. The motion is
scripted in units of the vehicle height ``H`` so it looks right for any design.
Axes match the viewport: +Y up, the vehicle's base rests on y=0.

Outcomes passed to ``conclude``
  LAND  the path reached the Moon: retro-burn and soft touchdown on the surface
  MISS  the vehicle could get there but the path misses: flies past, lost in space
  FALL  the vehicle cannot reach the Moon (delta-v): engine sputters out, falls back

``launch(liftoff=False)`` is the fourth failure: the engine ignites (if it has any
thrust) but the vehicle never leaves the pad.

States
  idle        vehicle on the pad, Moon hidden
  no_liftoff  engine strains on the pad; the vehicle stays put
  ascending   engine burning, climbing to a hover while the simulation runs
  descending  success: arcing to the Moon, flipping tail-first for a retro-burn
  landed      standing on the Moon
  flyby       failure: passing the Moon without reaching it
  lost        failure: gone into space
  falling     failure: engine out, tumbling back down
  crashed     failure: settled on the ground
"""

import math

import numpy as np

from spacecraft.geometry import rotate_z, rotation_between, translate

LAND = "land"
MISS = "miss"
FALL = "fall"
OUTCOMES = (LAND, MISS, FALL)

IDLE = "idle"
NO_LIFTOFF = "no_liftoff"
ASCENDING = "ascending"
DESCENDING = "descending"
LANDED = "landed"
FLYBY = "flyby"
LOST = "lost"
FALLING = "falling"
CRASHED = "crashed"

HOVER_HEIGHT = 4.5  # in vehicle heights
CLIMB_ACCEL = 0.9  # H / s^2
CLIMB_SPEED_LIMIT = 4.0  # H / s
GRAVITY = 1.6  # H / s^2 for the fall
DRIFT_SPEED = 0.12  # H / s sideways while falling
SPUTTER_TIME = 0.9  # s of failing engine before the fall
SETTLE_TIME = 0.5  # s for the wreck to finish tipping over
STRAIN_TIME = 3.0  # s the engine strains on the pad
LAND_TIME = 7.0  # s from hover to touchdown
FLYBY_TIME = 4.5  # s from hover to the closest approach
FLYBY_COAST = 3.0  # s drifting away before the vehicle is lost
PASS_DISTANCE = 1.8  # closest-approach distance for a miss, in Moon radii
FLASH_TIME = 1.6  # s
MOON_OFFSET = (6.0, 10.0, -3.0)  # Moon centre, in vehicle heights
MOON_RADIUS = 2.2  # in vehicle heights


def _smooth_toward(current: float, target: float, max_step: float) -> float:
    return current + float(np.clip(target - current, -max_step, max_step))


def _smoothstep(x: float) -> float:
    x = float(np.clip(x, 0.0, 1.0))
    return x * x * (3.0 - 2.0 * x)


def _unit(vector) -> np.ndarray:
    return vector / np.linalg.norm(vector)


class FlightAnimation:
    def __init__(self):
        self.reset()

    # -- setup ---------------------------------------------------------------

    def reset(self) -> None:
        self.state = IDLE
        self.time = 0.0
        self.height = 1.0  # H, the vehicle height
        self.core_radius = 0.5
        self.pivot = np.zeros(3)  # rest position of the vehicle centre
        self.position = np.zeros(3)
        self.velocity = np.zeros(3)
        self.tilt = 0.0  # radians, vehicle +Y tipping toward +X (falling)
        self.orientation = np.eye(4, dtype=np.float32)
        self.moon_center = np.zeros(3)
        self.moon_radius = 1.0
        self.flash_center = None
        self.flash_time = 0.0
        self.has_thrust = True
        self.landing_normal = np.array([0.0, 1.0, 0.0])
        self.closest_approach = None  # distance to the Moon centre on a miss
        self._fall_estimate = 1.0
        self._bezier = None
        self._exit = None
        self._pending = None  # a verdict held until the vehicle reaches its hover

    @property
    def pending(self) -> bool:
        """True while a verdict has arrived but the vehicle is still climbing."""
        return self._pending is not None

    @property
    def active(self) -> bool:
        return self.state != IDLE

    @property
    def burning(self) -> bool:
        if self.state == NO_LIFTOFF:
            return self.has_thrust and self.time < STRAIN_TIME
        if self.state in (ASCENDING, DESCENDING, FLYBY):
            return True
        if self.state == FALLING:  # a failing engine flickers out
            return self.time < SPUTTER_TIME and math.sin(self.time * 55.0) > -0.2 + self.time
        return False

    @property
    def vehicle_visible(self) -> bool:
        return self.state != LOST

    @property
    def moon_visible(self) -> bool:
        return self.active and self.state != NO_LIFTOFF

    @property
    def finished(self) -> bool:
        return self.state in (LANDED, LOST, CRASHED) or (
            self.state == NO_LIFTOFF and self.time >= STRAIN_TIME
        )

    def launch(
        self,
        center,
        height: float,
        core_radius: float,
        liftoff: bool = True,
        has_thrust: bool = True,
    ) -> None:
        """Start from the pad for a vehicle of this size (restarts any flight)."""
        self.reset()
        self.state = ASCENDING if liftoff else NO_LIFTOFF
        self.height = max(float(height), 1.0)
        self.core_radius = float(core_radius)
        self.has_thrust = bool(has_thrust)
        self.pivot = np.asarray(center, dtype=np.float64).copy()
        self.position = self.pivot.copy()
        self.moon_center = np.array(MOON_OFFSET) * self.height
        self.moon_radius = MOON_RADIUS * self.height

    def _at_hover(self) -> bool:
        lift = self.position[1] - self.pivot[1]
        return lift >= 0.97 * HOVER_HEIGHT * self.height

    def conclude(self, outcome: str) -> None:
        """Apply the mission verdict; only meaningful while ascending.

        A verdict that arrives before the vehicle has climbed to its hover point
        (a fast pre-check can answer in milliseconds) is held until it gets there,
        so every run visibly flies up before it succeeds or fails.
        """
        if outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome: {outcome}")
        if self.state != ASCENDING or self._pending is not None:
            return
        if not self._at_hover():
            self._pending = outcome
            return
        self._apply(outcome)

    def _apply(self, outcome: str) -> None:
        self.time = 0.0
        if outcome == LAND:
            self.state = DESCENDING
            self._start_landing()
        elif outcome == MISS:
            self.state = FLYBY
            self._start_flyby()
        else:
            self.state = FALLING
            self._start_fall()

    # -- stepping ------------------------------------------------------------

    def update(self, dt: float) -> None:
        dt = float(np.clip(dt, 0.0, 0.1))
        step = {
            ASCENDING: self._climb,
            NO_LIFTOFF: self._strain,
            DESCENDING: self._descend,
            FLYBY: self._flyby,
            FALLING: self._fall,
            CRASHED: self._settle,
            LANDED: self._rest,
            LOST: self._rest,
        }.get(self.state)
        if step is not None:
            step(dt)

    def _rest(self, dt: float) -> None:
        self.time += dt
        self.flash_time += dt

    def _climb(self, dt: float) -> None:
        H = self.height
        lift = self.position[1] - self.pivot[1]
        remaining = max(HOVER_HEIGHT * H - lift, 0.0)
        # Speed from which the vehicle can still stop at the hover point.
        braking = math.sqrt(2.0 * 0.8 * CLIMB_ACCEL * H * remaining)
        wanted = min(CLIMB_SPEED_LIMIT * H, braking)
        speed = _smooth_toward(self.velocity[1], wanted, CLIMB_ACCEL * H * dt)
        self.velocity[:] = (0.0, speed, 0.0)
        self.position += self.velocity * dt
        self.position[1] = min(self.position[1], self.pivot[1] + HOVER_HEIGHT * H)
        self.time += dt
        if self._pending is not None and self._at_hover():
            outcome, self._pending = self._pending, None
            self._apply(outcome)

    def _strain(self, dt: float) -> None:
        """Engine runs but thrust cannot overcome weight: shudder on the pad."""
        self.time += dt
        if self.has_thrust and self.time < STRAIN_TIME:
            shudder = abs(math.sin(self.time * 31.0)) * 0.012 * self.height
            self.position[1] = self.pivot[1] + shudder
        else:
            self.position[1] = self.pivot[1]

    # -- failure: fall -------------------------------------------------------

    def _start_fall(self) -> None:
        H = self.height
        self.velocity[0] = DRIFT_SPEED * H
        rise = self.position[1] - 0.25 * H
        speed = self.velocity[1]
        g = GRAVITY * H
        self._fall_estimate = max(0.5, (speed + math.sqrt(speed * speed + 2.0 * g * rise)) / g)

    def _floor_height(self, tilt: float) -> float:
        """Centre height at which the tipped vehicle just touches the ground."""
        return 0.5 * self.height * math.cos(tilt) + self.core_radius * math.sin(tilt)

    def _fall(self, dt: float) -> None:
        self.time += dt
        self.velocity[1] -= GRAVITY * self.height * dt
        self.position += self.velocity * dt
        progress = min(1.0, self.time / self._fall_estimate)
        self.tilt = (math.pi / 2.0) * progress**1.5
        floor = self._floor_height(self.tilt)
        if self.position[1] <= floor:
            self.position[1] = floor
            self.velocity[:] = 0.0
            self.state = CRASHED
            self.time = 0.0
            self.flash_center = np.array([self.position[0], 0.0, self.position[2]])
            self.flash_time = 0.0
        self.orientation = rotate_z(-self.tilt)

    def _settle(self, dt: float) -> None:
        self.time += dt
        self.flash_time += dt
        self.tilt = min(math.pi / 2.0, self.tilt + (math.pi / 2.0) * dt / SETTLE_TIME)
        self.position[1] = self._floor_height(self.tilt)
        self.orientation = rotate_z(-self.tilt)

    # -- Bezier paths --------------------------------------------------------

    def _set_path(self, start, end) -> None:
        # Leave straight up (matching the climb), then curve toward the end point.
        control = start + np.array([0.0, 0.45 * np.linalg.norm(end - start), 0.0])
        self._bezier = (start, control, end)

    def _bezier_point(self, s: float):
        p0, p1, p2 = self._bezier
        point = (1 - s) ** 2 * p0 + 2 * (1 - s) * s * p1 + s**2 * p2
        tangent = 2 * (1 - s) * (p1 - p0) + 2 * s * (p2 - p1)
        return point, tangent

    # -- success: land -------------------------------------------------------

    def _start_landing(self) -> None:
        start = self.position.copy()
        normal = _unit(start - self.moon_center)  # near side, facing the vehicle
        self.landing_normal = normal
        standing = self.moon_radius + 0.5 * self.height  # centre height, base on the surface
        self._set_path(start, self.moon_center + normal * standing)

    def _descend(self, dt: float) -> None:
        self.time += dt
        u = min(1.0, self.time / LAND_TIME)
        # Ease in and out so the vehicle leaves the hover and touches down at rest.
        point, _ = self._bezier_point(_smoothstep(u))
        # Never let the nose clip the surface on the way in.
        offset = point - self.moon_center
        floor = self.moon_radius + 0.5 * self.height
        distance = np.linalg.norm(offset)
        if distance < floor:
            point = self.moon_center + offset / distance * floor
        self.position = point
        # Rotate from upright to standing on the surface (engine toward the Moon).
        self.orientation = rotation_between(
            (0.0, 1.0, 0.0), self.landing_normal, _smoothstep((u - 0.1) / 0.8)
        )
        if u >= 1.0:
            self.state = LANDED
            self.time = 0.0
            self.flash_time = 0.0

    # -- failure: miss -------------------------------------------------------

    def _start_flyby(self) -> None:
        start = self.position.copy()
        toward = _unit(self.moon_center - start)
        side = np.cross(toward, (0.0, 1.0, 0.0))
        side = np.array([1.0, 0.0, 0.0]) if np.linalg.norm(side) < 1e-6 else _unit(side)
        closest = self.moon_center + side * PASS_DISTANCE * self.moon_radius
        self.closest_approach = PASS_DISTANCE * self.moon_radius
        self._set_path(start, closest)
        # Exit velocity of the accelerating path, held constant afterwards.
        _, tangent = self._bezier_point(1.0)
        self._exit = (closest, _unit(tangent), float(np.linalg.norm(tangent)) * 2.0 / FLYBY_TIME)

    def _flyby(self, dt: float) -> None:
        self.time += dt
        if self.time < FLYBY_TIME:
            point, tangent = self._bezier_point((self.time / FLYBY_TIME) ** 2)
            direction = _unit(tangent)
        else:
            closest, direction, speed = self._exit
            point = closest + direction * speed * (self.time - FLYBY_TIME)
            if self.time >= FLYBY_TIME + FLYBY_COAST:
                self.state = LOST
                self.time = 0.0
        self.position = point
        self.orientation = rotation_between((0.0, 1.0, 0.0), direction)

    # -- outputs for drawing -------------------------------------------------

    def vehicle_matrix(self) -> np.ndarray:
        """World transform for the vehicle frame (identity while on the pad)."""
        return (
            translate(*self.position)
            @ self.orientation
            @ translate(*(-self.pivot))
        ).astype(np.float32)

    def flame_length(self) -> float:
        flicker = 1.0 + 0.15 * math.sin(self.time * 45.0) + 0.08 * math.sin(self.time * 71.0)
        length = 0.45 * self.height * flicker
        if self.state == FALLING:
            length *= max(0.0, 1.0 - self.time / SPUTTER_TIME)
        elif self.state == NO_LIFTOFF:
            length *= 0.45  # a labouring engine, not a full burn
        return length

    def flash(self):
        """(centre, radius, fade 1->0) of the crash flash, or None."""
        if self.flash_center is None or self.flash_time >= FLASH_TIME:
            return None
        t = self.flash_time / FLASH_TIME
        return self.flash_center, self.height * (0.6 + 2.2 * t), 1.0 - t

    def focus(self):
        """(centre, radius) the camera should keep in view."""
        H = self.height
        if self.state == NO_LIFTOFF:
            return self.pivot.copy(), 1.2 * H
        if self.state in (FALLING, CRASHED):
            y = float(self.position[1])
            return np.array([self.position[0], y * 0.5, self.position[2]]), y * 0.5 + 2.5 * H
        if self.state == LANDED:
            return self.position.copy(), 2.2 * H
        if self.state == LOST:
            return self.moon_center.copy(), 2.2 * self.moon_radius
        # Climbing, landing approach, flyby: keep the vehicle and the Moon in frame.
        centre = (self.position + self.moon_center) / 2.0
        radius = float(np.linalg.norm(self.moon_center - self.position)) / 2.0
        return centre, radius + self.moon_radius + H
