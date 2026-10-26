# camera.py

import numpy as np


class Camera:
    def __init__(self):
        self.offset = np.array([0.0, 0.0], dtype=np.float32)
        self.zoom = 1.0

        self.dragging = False
        self.last_mouse = None

    def handle_input(self, window):

        cursor = np.array(window.get_cursor_pos())

        # Start drag
        if window.is_pressed(ti.ui.LMB):
            if not self.dragging:
                self.dragging = True
                self.last_mouse = cursor
            else:
                delta = cursor - self.last_mouse

                self.offset[0] -= delta[0] / self.zoom
                self.offset[1] += delta[1] / self.zoom

                self.last_mouse = cursor
        else:
            self.dragging = False

    def zoom_in(self, amount=1.1):
        self.zoom *= amount

    def zoom_out(self, amount=1.1):
        self.zoom /= amount