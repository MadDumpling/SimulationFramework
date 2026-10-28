import numpy as np
import dearpygui.dearpygui as dpg

from .renderer import Renderer


class DpgRenderer(Renderer):

    def __init__(
        self,
        width=1280,
        height=720,
        texture_tag="viewport_texture",
    ):
        self.width = width
        self.height = height
        self.texture_tag = texture_tag

        self.frame = np.zeros(
            (self.height, self.width, 4),
            dtype=np.float32,
        )

    @property
    def name(self):
        return "CPU Framebuffer"

    @property
    def running(self):
        return True

    def begin_frame(self):
        self.frame[:, :, 0] = 0.05
        self.frame[:, :, 1] = 0.05
        self.frame[:, :, 2] = 0.08
        self.frame[:, :, 3] = 1.0

    def _to_points(self, positions):
        if hasattr(positions, "to_numpy"):
            return positions.to_numpy()

        return np.asarray(
            positions,
            dtype=np.float32,
        )

    def draw_circles(
        self,
        positions,
        radius,
        color,
    ):
        points = self._to_points(
            positions,
        )

        if points.size == 0:
            return

        radius_pixels = max(
            1,
            int(
                radius * min(
                    self.width,
                    self.height,
                )
            ),
        )

        for point in points:
            cx = int(point[0] * self.width)
            cy = int((1.0 - point[1]) * self.height)

            x0 = max(0, cx - radius_pixels)
            x1 = min(
                self.width - 1,
                cx + radius_pixels,
            )

            y0 = max(0, cy - radius_pixels)
            y1 = min(
                self.height - 1,
                cy + radius_pixels,
            )

            if x0 > x1 or y0 > y1:
                continue

            yy, xx = np.ogrid[
                y0:y1 + 1,
                x0:x1 + 1,
            ]

            mask = (
                (xx - cx) ** 2
                + (yy - cy) ** 2
            ) <= radius_pixels ** 2

            region = self.frame[
                y0:y1 + 1,
                x0:x1 + 1,
            ]

            region[mask, 0] = color[0]
            region[mask, 1] = color[1]
            region[mask, 2] = color[2]
            region[mask, 3] = 1.0

    def draw_lines(
        self,
        start,
        end,
        color,
    ):
        _ = start
        _ = end
        _ = color

    def draw_points(
        self,
        positions,
        color,
    ):
        points = self._to_points(
            positions,
        )

        if points.size == 0:
            return

        for point in points:
            px = int(point[0] * self.width)
            py = int((1.0 - point[1]) * self.height)

            if (
                0 <= px < self.width
                and 0 <= py < self.height
            ):
                self.frame[py, px, 0] = color[0]
                self.frame[py, px, 1] = color[1]
                self.frame[py, px, 2] = color[2]
                self.frame[py, px, 3] = 1.0

    def end_frame(self):
        if not dpg.does_item_exist(
            self.texture_tag,
        ):
            return

        dpg.set_value(
            self.texture_tag,
            self.frame.reshape(-1).tolist(),
        )
