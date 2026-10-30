import dearpygui.dearpygui as dpg


class DpgInputSource:
    """Mouse state for the viewport image, in viewport-relative terms."""

    def __init__(
        self,
        viewport_image_tag="viewport_image",
    ):
        self.viewport_image_tag = viewport_image_tag
        self._scroll = 0.0
        self._last_mouse = None

        with dpg.handler_registry():
            dpg.add_mouse_wheel_handler(callback=self._on_wheel)

    def _on_wheel(self, sender, app_data):
        self._scroll += app_data

    def consume_scroll(self):
        scroll, self._scroll = self._scroll, 0.0
        return scroll

    def _get_viewport_rect(self):
        if not dpg.does_item_exist(self.viewport_image_tag):
            return None

        min_x, min_y = dpg.get_item_rect_min(self.viewport_image_tag)
        max_x, max_y = dpg.get_item_rect_max(self.viewport_image_tag)
        return (min_x, min_y, max_x, max_y)

    def is_cursor_over_viewport(self):
        rect = self._get_viewport_rect()
        if rect is None:
            return False

        mouse_x, mouse_y = dpg.get_mouse_pos(local=False)
        min_x, min_y, max_x, max_y = rect
        return min_x <= mouse_x <= max_x and min_y <= mouse_y <= max_y

    def get_cursor_pos(self):
        """Normalized cursor position over the image, origin bottom-left."""
        rect = self._get_viewport_rect()
        if rect is None:
            return (0.5, 0.5)

        mouse_x, mouse_y = dpg.get_mouse_pos(local=False)
        min_x, min_y, max_x, max_y = rect
        width = max(1.0, max_x - min_x)
        height = max(1.0, max_y - min_y)

        x = min(1.0, max(0.0, (mouse_x - min_x) / width))
        y = min(1.0, max(0.0, 1.0 - (mouse_y - min_y) / height))
        return (x, y)

    def get_window_shape(self):
        rect = self._get_viewport_rect()
        if rect is None:
            return (1.0, 1.0)

        min_x, min_y, max_x, max_y = rect
        return (max(1.0, max_x - min_x), max(1.0, max_y - min_y))

    def mouse_delta(self):
        """Pixel movement since the previous call, in image pixels."""
        mouse = dpg.get_mouse_pos(local=False)
        last, self._last_mouse = self._last_mouse, mouse
        if last is None:
            return (0.0, 0.0)
        return (mouse[0] - last[0], mouse[1] - last[1])

    def is_down(self, button):
        buttons = {
            "left": dpg.mvMouseButton_Left,
            "right": dpg.mvMouseButton_Right,
            "middle": dpg.mvMouseButton_Middle,
        }
        return dpg.is_mouse_button_down(buttons[button])

    def is_clicked(self, button):
        buttons = {
            "left": dpg.mvMouseButton_Left,
            "right": dpg.mvMouseButton_Right,
            "middle": dpg.mvMouseButton_Middle,
        }
        return dpg.is_mouse_button_clicked(buttons[button])

    def is_pressed(self, key):
        key_map = {"f": dpg.mvKey_F, "r": dpg.mvKey_R}
        mapped = key_map.get(key.lower())
        return mapped is not None and dpg.is_key_pressed(mapped)
