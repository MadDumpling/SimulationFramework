from registry import (
    SIMULATIONS,
    register_simulation,
)


def test_register_simulation():

    @register_simulation
    class TestSimulation:
        name = "Test Simulation"

    assert (
        "Test Simulation"
        in SIMULATIONS
    )

    assert (
        SIMULATIONS["Test Simulation"]
        == TestSimulation
    )
