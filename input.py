import numpy as np
import taichi as ti


class Camera:
    def __init__(self):
        self.offset = np.array([0.0, 0.0], dtype=np.float32)
        self.zoom = 1.0

        self.dragging = False
        self.last_mouse = None

    def reset(self):
        self.offset[:] = 0.0
        self.zoom = 1.0
        self.dragging = False
        self.last_mouse = None

    def update(self, window, allow_mouse_drag=True):
        if not allow_mouse_drag:
            self.dragging = False
            self.last_mouse = None
            return

        mouse = np.array(window.get_cursor_pos(), dtype=np.float32)

        # Right mouse drag keeps left-click UI interaction separate from the camera.
        if window.is_pressed(ti.ui.RMB):

            if not self.dragging:
                self.dragging = True
                self.last_mouse = mouse

            else:
                delta = mouse - self.last_mouse

                self.offset[0] -= delta[0] / self.zoom
                self.offset[1] += delta[1] / self.zoom

                self.last_mouse = mouse

        else:
            self.dragging = False

    def zoom_at(self, factor, mouse_pos):
        mouse = np.array(mouse_pos, dtype=np.float32)

        before = (mouse - 0.5) / self.zoom + self.offset

        self.zoom *= factor

        self.zoom = max(0.1, min(self.zoom, 100.0))

        after = (mouse - 0.5) / self.zoom + self.offset

        self.offset += before - after


class InputManager:
    def __init__(self):
        self.camera = Camera()

    def update(self, window, disable_mouse_camera=False):

        self.camera.update(
            window,
            allow_mouse_drag=not disable_mouse_camera,
        )

        if window.is_pressed("r"):
            self.camera.reset()

        # Zoom
        if window.is_pressed("e"):
            self.camera.zoom *= 1.02

        if window.is_pressed("q"):
            self.camera.zoom /= 1.02

        self.camera.zoom = max(
            0.1,
            min(self.camera.zoom, 20.0)
        )

        # Camera movement
        speed = 0.01 / self.camera.zoom


        if window.is_pressed("w"):
            self.camera.offset[1] += speed

        if window.is_pressed("s"):
            self.camera.offset[1] -= speed

        if window.is_pressed("a"):
            self.camera.offset[0] -= speed

        if window.is_pressed("d"):
            self.camera.offset[0] += speed
