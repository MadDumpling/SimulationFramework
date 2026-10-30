from unittest.mock import Mock, patch

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

    def load(self, name):
        pass

    def reset(self):
        pass


def create_ui():

    manager = MockSimulationManager()

    events = Mock()

    ui = SimulationUI(
        manager,
        events,
    )

    return (
        ui,
        manager,
        events,
    )


def test_pause_toggle():

    ui, _, _ = create_ui()

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

    ui, _, _ = create_ui()

    parameter = MockParameter()

    ui.update_parameter(
        None,
        12.5,
        parameter,
    )

    assert parameter.value == 12.5


def test_reset_callback():

    ui, _, events = create_ui()

    ui.reset_simulation(
        None,
        None,
        None,
    )

    events.publish.assert_called_once_with(
        "simulation.reset"
    )


def test_change_simulation():

    ui, _, events = create_ui()

    with patch.object(
        ui,
        "rebuild_parameter_ui",
    ) as mock_rebuild:

        ui.change_simulation(
            None,
            "Bouncing Balls",
            None,
        )

    events.publish.assert_called_once_with(
        "simulation.load",
        "Bouncing Balls",
    )

    mock_rebuild.assert_called_once()