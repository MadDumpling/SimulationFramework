from simulations.bouncing_balls import (
    BouncingBalls
)


def test_metadata():

    assert (
        BouncingBalls.name
        == "Bouncing Balls"
    )

    assert (
        BouncingBalls.author
        == "You"
    )

    assert (
        BouncingBalls.version
        == "0.3"
    )