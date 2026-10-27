from plugin_loader import (
    load_simulations
)

from registry import (
    create_simulation
)


def test_simulation_creation():

    load_simulations()

    simulation = create_simulation(
        "Bouncing Balls"
    )

    assert simulation is not None