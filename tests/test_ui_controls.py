from ui.controls import SimulationUI


class DummyWindow:
    def __init__(self, cursor_pos, window_shape=(1920, 1080)):
        self._cursor_pos = cursor_pos
        self._window_shape = window_shape

    def get_cursor_pos(self):
        return self._cursor_pos

    def get_window_shape(self):
        return self._window_shape


def test_is_mouse_over_gui_with_normalized_coords():
    ui = SimulationUI()
    window = DummyWindow((0.10, 0.10))

    assert ui.is_mouse_over_gui(window) is True


def test_is_mouse_over_gui_outside_with_normalized_coords():
    ui = SimulationUI()
    window = DummyWindow((0.60, 0.60))

    assert ui.is_mouse_over_gui(window) is False


def test_is_mouse_over_gui_with_pixel_coords():
    ui = SimulationUI()
    window = DummyWindow((192, 108), window_shape=(1920, 1080))

    assert ui.is_mouse_over_gui(window) is True
