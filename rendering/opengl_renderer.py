import dearpygui.dearpygui as dpg
import moderngl
import numpy as np

from .renderer import Renderer


VERTEX_SHADER = """
#version 330

in vec2 in_position;

uniform float point_size;

void main()
{
    gl_Position = vec4(
        in_position,
        0.0,
        1.0
    );

    gl_PointSize = point_size;
}
"""


FRAGMENT_SHADER = """
#version 330

uniform vec3 color;

out vec4 fragColor;

void main()
{
    vec2 uv =
        gl_PointCoord
        - vec2(0.5);

    if (length(uv) > 0.5)
    {
        discard;
    }

    fragColor = vec4(
        color,
        1.0
    );
}
"""


class OpenGLRenderer(Renderer):

    DEFAULT_WIDTH = 1280
    DEFAULT_HEIGHT = 720

    BACKGROUND_COLOR = (
        0.05,
        0.05,
        0.08,
        1.0,
    )

    def __init__(self):

        self.width = self.DEFAULT_WIDTH
        self.height = self.DEFAULT_HEIGHT

        self.ctx = (
            moderngl.create_standalone_context()
        )

        self.ctx.enable(
            moderngl.PROGRAM_POINT_SIZE
        )

        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER,
        )

        self._create_render_target()

        self.last_debug_radius = None

        print("OpenGL initialized")

        print(
            "Renderer:",
            self.ctx.info.get(
                "GL_RENDERER"
            ),
        )

        print(
            "Vendor:",
            self.ctx.info.get(
                "GL_VENDOR"
            ),
        )

        print(
            "Version:",
            self.ctx.info.get(
                "GL_VERSION"
            ),
        )

    def _create_render_target(self):

        self.texture = self.ctx.texture(
            (
                self.width,
                self.height,
            ),
            4,
            dtype="f1",
        )

        self.fbo = self.ctx.framebuffer(
            color_attachments=[
                self.texture
            ]
        )

    def resize(
        self,
        width,
        height,
    ):

        width = max(
            1,
            int(width),
        )

        height = max(
            1,
            int(height),
        )

        if (
            width == self.width
            and height == self.height
        ):
            return

        self.width = width
        self.height = height

        if hasattr(
            self,
            "texture",
        ):
            self.texture.release()

        if hasattr(
            self,
            "fbo",
        ):
            self.fbo.release()

        self._create_render_target()

        print(
            f"Renderer resized: "
            f"{width}x{height}"
        )

    @property
    def name(self):
        return "OpenGL"

    @property
    def running(self):
        return True

    def begin_frame(self):

        self.fbo.use()

        self.ctx.clear(
            *self.BACKGROUND_COLOR
        )

    def clear(
        self,
        color,
    ):

        self.ctx.clear(
            color[0],
            color[1],
            color[2],
            1.0,
        )

    def _to_numpy(
        self,
        positions,
    ):

        if hasattr(
            positions,
            "to_numpy",
        ):
            return (
                positions.to_numpy()
            )

        return np.asarray(
            positions,
            dtype="f4",
        )

    def _to_gl_space(
        self,
        points,
    ):

        return np.asarray(
            (
                points * 2.0
            ) - 1.0,
            dtype="f4",
        )

    def _create_geometry(
        self,
        points,
    ):

        vbo = self.ctx.buffer(
            points.tobytes()
        )

        vao = self.ctx.vertex_array(
            self.program,
            [
                (
                    vbo,
                    "2f",
                    "in_position",
                )
            ],
        )

        return vbo, vao

    def radius_to_pixels(
        self,
        radius,
    ):

        return max(
            1.0,
            radius
            * min(
                self.width,
                self.height,
            )
            * 2.0,
        )

    def draw_points(
        self,
        positions,
        color,
    ):

        points = self._to_numpy(
            positions
        )

        if len(points) == 0:
            return

        gl_points = (
            self._to_gl_space(
                points
            )
        )

        self.program[
            "point_size"
        ].value = 4.0

        self.program[
            "color"
        ].value = color

        _, vao = (
            self._create_geometry(
                gl_points
            )
        )

        vao.render(
            moderngl.POINTS
        )

    def draw_circles(
        self,
        positions,
        radius,
        color,
    ):

        points = self._to_numpy(
            positions
        )

        if len(points) == 0:
            return

        point_size = (
            self.radius_to_pixels(
                radius
            )
        )

        if (
            radius
            != self.last_debug_radius
        ):

            self.last_debug_radius = (
                radius
            )

            print(
                f"Radius={radius}"
                f" Size={point_size}"
            )

        gl_points = (
            self._to_gl_space(
                points
            )
        )

        self.program[
            "point_size"
        ].value = point_size

        self.program[
            "color"
        ].value = color

        _, vao = (
            self._create_geometry(
                gl_points
            )
        )

        vao.render(
            moderngl.POINTS
        )

    def draw_lines(
        self,
        start,
        end,
        color,
    ):
        pass

    def end_frame(self):

        pixels = (
            self.texture.read()
        )

        frame = np.frombuffer(
            pixels,
            dtype=np.uint8,
        )
        print(
            "frame elements:",
            len(frame)
        )
        frame = frame.reshape(
            (
                self.height,
                self.width,
                4,
            )
        )

        frame = (
            frame.astype(
                np.float32
            )
            / 255.0
        )

        frame = np.flipud(
            frame
        )

        if dpg.does_item_exist(
            "viewport_texture"
        ):

            dpg.set_value(
                "viewport_texture",
                frame.reshape(-1),
            )
    print(
        "texture exists:",
        dpg.does_item_exist(
            "viewport_texture"
        )
    )

    print(
        "image exists:",
        dpg.does_item_exist(
            "viewport_image"
        )
    )

    try:

        dpg.set_value(
            "viewport_texture",
            frame.reshape(-1),
        )

        print(
            "upload success",
            len(
                frame.reshape(-1)
            )
        )

    except Exception as e:

        print(
            "UPLOAD ERROR:",
            e,
        )