from rendering import (
    OpenGLRenderer,
)
import numpy as np

from rendering import opengl_renderer


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


def test_end_frame_reads_pixels_and_uploads_normalized_top_down_texture(
    monkeypatch,
):
    renderer = OpenGLRenderer.__new__(OpenGLRenderer)
    renderer.width = 2
    renderer.height = 2

    bottom_up_pixels = np.array(
        [
            [[255, 0, 0, 255], [0, 255, 0, 255]],
            [[0, 0, 255, 255], [255, 255, 255, 255]],
        ],
        dtype=np.uint8,
    )
    read_calls = []

    class FakeTexture:
        def read(self):
            read_calls.append(True)
            return bottom_up_pixels.tobytes()

    renderer.texture = FakeTexture()
    renderer._frame_upload = np.empty((2, 2, 4), dtype=np.float32)
    uploads = []
    monkeypatch.setattr(
        opengl_renderer.dpg,
        "does_item_exist",
        lambda tag: tag == "viewport_texture",
    )
    monkeypatch.setattr(
        opengl_renderer.dpg,
        "set_value",
        lambda tag, value: uploads.append((tag, value)),
    )

    renderer.end_frame()

    assert read_calls == [True]
    assert len(uploads) == 1
    tag, uploaded_data = uploads[0]
    assert tag == "viewport_texture"
    assert uploaded_data.shape == (16,)
    assert uploaded_data.dtype == np.float32
    np.testing.assert_allclose(
        uploaded_data.reshape((2, 2, 4)),
        bottom_up_pixels[::-1].astype(np.float32) / 255.0,
    )


def test_end_frame_skips_dpg_update_without_viewport_texture(monkeypatch):
    renderer = OpenGLRenderer.__new__(OpenGLRenderer)
    renderer.width = 1
    renderer.height = 1
    renderer.texture = type(
        "FakeTexture",
        (),
        {"read": lambda self: bytes((0, 0, 0, 255))},
    )()
    renderer._frame_upload = np.empty((1, 1, 4), dtype=np.float32)
    uploads = []
    monkeypatch.setattr(
        opengl_renderer.dpg,
        "does_item_exist",
        lambda _tag: False,
    )
    monkeypatch.setattr(
        opengl_renderer.dpg,
        "set_value",
        lambda *args: uploads.append(args),
    )

    renderer.end_frame()

    assert uploads == []