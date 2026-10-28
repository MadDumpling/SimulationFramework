from rendering import (
    OpenGLRenderer,
)


def test_opengl_context_created():

    renderer = (
        OpenGLRenderer()
    )

    assert (
        renderer.ctx
        is not None
    )


def test_fbo_created():

    renderer = (
        OpenGLRenderer()
    )

    assert (
        renderer.fbo
        is not None
    )


def test_texture_created():

    renderer = (
        OpenGLRenderer()
    )

    assert (
        renderer.texture
        is not None
    )