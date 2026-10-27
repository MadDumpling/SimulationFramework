from simulations.boids import (
    Boids,
)


def test_boids_metadata():

    assert (
        Boids.name
        == "Boids"
    )

    assert (
        Boids.author
        == "You"
    )