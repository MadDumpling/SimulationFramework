"""Turntable orbit camera for the 3D spacecraft viewport."""

import math

import numpy as np

MIN_PITCH = math.radians(-85.0)
MAX_PITCH = math.radians(85.0)


def look_at(eye, target, up=(0.0, 1.0, 0.0)) -> np.ndarray:
    eye = np.asarray(eye, dtype=np.float64)
    forward = np.asarray(target, dtype=np.float64) - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, forward)
    view = np.eye(4)
    view[0, :3] = right
    view[1, :3] = true_up
    view[2, :3] = -forward
    view[:3, 3] = -view[:3, :3] @ eye
    return view.astype(np.float32)


def perspective(fov_y: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(fov_y / 2.0)
    projection = np.zeros((4, 4), dtype=np.float32)
    projection[0, 0] = f / aspect
    projection[1, 1] = f
    projection[2, 2] = (far + near) / (near - far)
    projection[2, 3] = 2.0 * far * near / (near - far)
    projection[3, 2] = -1.0
    return projection


class OrbitCamera:
    FOV_Y = math.radians(40.0)

    def __init__(self):
        self.target = np.zeros(3, dtype=np.float32)
        self.yaw = math.radians(35.0)
        self.pitch = math.radians(18.0)
        self.distance = 10.0
        self.min_distance = 1.0
        self.max_distance = 500.0

    def frame(self, center, radius: float) -> None:
        """Fit a bounding sphere in view, keeping the current orientation."""
        self.target = np.asarray(center, dtype=np.float32).copy()
        self.min_distance = max(0.2, radius * 0.25)
        self.max_distance = max(50.0, radius * 20.0)
        fit = radius / math.sin(self.FOV_Y / 2.0) * 1.05
        self.distance = float(np.clip(fit, self.min_distance, self.max_distance))

    def follow(self, center, radius: float, dt: float, rate: float = 3.0) -> None:
        """Ease the target and distance toward keeping a bounding sphere in view."""
        blend = 1.0 - math.exp(-rate * max(dt, 0.0))
        fit = max(radius, 1.0) / math.sin(self.FOV_Y / 2.0) * 1.1
        self.max_distance = max(self.max_distance, fit * 1.5)
        self.target = self.target + (np.asarray(center, dtype=np.float32) - self.target) * blend
        self.distance = float(
            np.clip(
                self.distance + (fit - self.distance) * blend,
                self.min_distance,
                self.max_distance,
            )
        )

    def orbit(self, dx_pixels: float, dy_pixels: float, sensitivity: float = 0.008) -> None:
        self.yaw -= dx_pixels * sensitivity
        self.pitch = float(
            np.clip(self.pitch + dy_pixels * sensitivity, MIN_PITCH, MAX_PITCH)
        )

    def pan(self, dx_pixels: float, dy_pixels: float, viewport_height: float) -> None:
        world_per_pixel = (
            2.0 * self.distance * math.tan(self.FOV_Y / 2.0) / max(1.0, viewport_height)
        )
        view = self.view_matrix()
        right, up = view[0, :3], view[1, :3]
        self.target = self.target + (
            -right * dx_pixels + up * dy_pixels
        ) * world_per_pixel

    def zoom(self, wheel_steps: float) -> None:
        self.distance = float(
            np.clip(
                self.distance * (0.88**wheel_steps),
                self.min_distance,
                self.max_distance,
            )
        )

    @property
    def eye(self) -> np.ndarray:
        offset = self.distance * np.array(
            [
                math.cos(self.pitch) * math.sin(self.yaw),
                math.sin(self.pitch),
                math.cos(self.pitch) * math.cos(self.yaw),
            ]
        )
        return (self.target + offset).astype(np.float32)

    def view_matrix(self) -> np.ndarray:
        return look_at(self.eye, self.target)

    def view_projection(self, aspect: float) -> np.ndarray:
        near = max(0.05, self.distance * 0.02)
        far = self.distance + self.max_distance * 2.0
        return perspective(self.FOV_Y, aspect, near, far) @ self.view_matrix()
