from rendering import (
    DpgRenderer,
    OpenGLRenderer,
)


def test_dpg_renderer_name():

    renderer = DpgRenderer()

    assert renderer.name == (
        "CPU Framebuffer"
    )


def test_opengl_renderer_name():

    renderer = OpenGLRenderer()

    assert renderer.name == (
        "OpenGL"
    )


def test_renderers_running():

    assert (
        DpgRenderer()
        .running
        is True
    )

    assert (
        OpenGLRenderer()
        .running
        is True
    )