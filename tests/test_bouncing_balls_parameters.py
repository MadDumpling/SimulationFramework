from simulations.bouncing_balls import (
    BouncingBalls
)


def test_parameter_registration():

    simulation = BouncingBalls()

    assert (
        "gravity"
        in simulation.parameters
    )

    assert (
        "damping"
        in simulation.parameters
    )

    assert (
        "radius"
        in simulation.parameters
    )