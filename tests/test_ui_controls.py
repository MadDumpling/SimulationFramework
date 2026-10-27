from unittest.mock import patch

from ui.controls import SimulationUI


class MockParameter:

    def __init__(self):
        self.name = "Gravity"
        self.value = 5.0
        self.min = 0.0
        self.max = 10.0


class MockSimulation:

    def __init__(self):
        self.parameters = {
            "gravity": MockParameter()
        }


class MockSimulationManager:

    def __init__(self):
        self.current = MockSimulation()
        self.loaded_name = None
        self.was_reset = False

    def load(self, name):
        self.loaded_name = name

    def reset(self):
        self.was_reset = True


def test_pause_toggle():

    manager = MockSimulationManager()

    ui = SimulationUI(manager)

    ui.toggle_pause(
        None,
        True,
        None,
    )

    assert ui.paused is True

    ui.toggle_pause(
        None,
        False,
        None,
    )

    assert ui.paused is False


def test_parameter_update():

    manager = MockSimulationManager()

    ui = SimulationUI(manager)

    parameter = MockParameter()

    ui.update_parameter(
        None,
        12.5,
        parameter,
    )

    assert parameter.value == 12.5


def test_reset_callback():

    manager = MockSimulationManager()

    ui = SimulationUI(manager)

    ui.reset_simulation(
        None,
        None,
        None,
    )

    assert manager.was_reset is True


def test_change_simulation():

    manager = MockSimulationManager()

    ui = SimulationUI(manager)

    with patch.object(
        ui,
        "rebuild_parameter_ui"
    ) as mock_rebuild:

        ui.change_simulation(
            None,
            "Bouncing Balls",
            None,
        )

    assert (
        manager.loaded_name
        == "Bouncing Balls"
    )

    mock_rebuild.assert_called_once()