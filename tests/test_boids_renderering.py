from simulations.boids import (
    Boids,
)
from rendering import (
    OpenGLRenderer,
)


def test_boids_render():

    simulation = (
        Boids()
    )

    renderer = (
        OpenGLRenderer()
    )

    class Camera:

        offset = (
            0.0,
            0.0,
        )

        zoom = 1.0

    simulation.render(
        renderer,
        Camera(),
    )
