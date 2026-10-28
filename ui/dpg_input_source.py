import dearpygui.dearpygui as dpg


class DpgInputSource:

    def __init__(
        self,
        viewport_image_tag="viewport_image",
    ):
        self.viewport_image_tag = viewport_image_tag

    def _get_viewport_rect(self):
        if not dpg.does_item_exist(
            self.viewport_image_tag,
        ):
            return None

        min_x, min_y = dpg.get_item_rect_min(
            self.viewport_image_tag
        )

        max_x, max_y = dpg.get_item_rect_max(
            self.viewport_image_tag
        )

        return (
            min_x,
            min_y,
            max_x,
            max_y,
        )

    def is_cursor_over_viewport(self):
        rect = self._get_viewport_rect()

        if rect is None:
            return False

        mouse_x, mouse_y = dpg.get_mouse_pos(
            local=False
        )

        min_x, min_y, max_x, max_y = rect

        return (
            min_x <= mouse_x <= max_x
            and min_y <= mouse_y <= max_y
        )

    def get_cursor_pos(self):
        rect = self._get_viewport_rect()

        if rect is None:
            return (0.5, 0.5)

        mouse_x, mouse_y = dpg.get_mouse_pos(
            local=False
        )

        min_x, min_y, max_x, max_y = rect

        width = max(1.0, max_x - min_x)
        height = max(1.0, max_y - min_y)

        x = (mouse_x - min_x) / width
        y = 1.0 - ((mouse_y - min_y) / height)

        x = min(1.0, max(0.0, x))
        y = min(1.0, max(0.0, y))

        return (x, y)

    def get_window_shape(self):
        rect = self._get_viewport_rect()

        if rect is None:
            return (1.0, 1.0)

        min_x, min_y, max_x, max_y = rect

        return (
            max(1.0, max_x - min_x),
            max(1.0, max_y - min_y),
        )

    def is_pressed(self, key):
        if key == "mouse_right":
            return dpg.is_mouse_button_down(
                dpg.mvMouseButton_Right
            )

        key_map = {
            "w": dpg.mvKey_W,
            "a": dpg.mvKey_A,
            "s": dpg.mvKey_S,
            "d": dpg.mvKey_D,
            "q": dpg.mvKey_Q,
            "e": dpg.mvKey_E,
            "r": dpg.mvKey_R,
        }

        mapped = key_map.get(key.lower())

        if mapped is None:
            return False

        return dpg.is_key_down(mapped)
