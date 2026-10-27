from plugin_loader import (
    load_simulations
)

from simulation_manager import (
    SimulationManager
)


def test_load_simulation():

    load_simulations()

    manager = SimulationManager()

    manager.load(
        "Bouncing Balls"
    )

    assert manager.current is not None