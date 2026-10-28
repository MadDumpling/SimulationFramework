from rendering import (
    OpenGLRenderer,
)


def test_radius_conversion():

    renderer = (
        OpenGLRenderer()
    )

    size = (
        renderer.radius_to_pixels(
            0.005
        )
    )

    assert size == 7.2