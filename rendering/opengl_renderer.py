# Opengl_renderer.py
import moderngl
import numpy as np

from .renderer import Renderer
import moderngl
import numpy as np
import dearpygui.dearpygui as dpg

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

    if (
        length(uv)
        > 0.5
    )
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

    def __init__(self):


        self.width = 1280
        self.height = 720

        self.ctx = (
            moderngl
            .create_standalone_context()
        )
        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER,
        )
        print(
            self.program._members.keys()
        )
        self.program["point_size"].value = 30.0
        self.program["color"].value = (
            1.0,
            1.0,
            1.0,
        )
        self.texture = (
            self.ctx.texture(
                (self.width, self.height),
                4,
                dtype="f1",
            )
        )

        self.fbo = (
            self.ctx.framebuffer(
                color_attachments=[
                    self.texture
                ]
            )
        )

        print(
            "OpenGL initialized"
        )
        print("Renderer:", self.ctx.info.get("GL_RENDERER"))
        print("Vendor:", self.ctx.info.get("GL_VENDOR"))
        print("Version:", self.ctx.info.get("GL_VERSION"))
        self.ctx.enable(
            moderngl.PROGRAM_POINT_SIZE
        )
        self.last_debug_radius = None
    @property
    def name(self):
        return "OpenGL"

    @property
    def running(self):
        return True

    def begin_frame(self):
        
        self.fbo.use()
        self.ctx.clear(
            0.05,
            0.05,
            0.08,
            1.0,
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

    def draw_points(
        self,
        positions,
        color,
    ):

        if hasattr(
            positions,
            "to_numpy",
        ):
            points = (
                positions.to_numpy()
            )

        else:
            points = np.asarray(
                positions,
                dtype="f4",
            )

        if len(points) == 0:
            return

        #
        # [0,1] → OpenGL [-1,1]
        #

        gl_points = (
            points * 2.0
        ) - 1.0

        gl_points = np.asarray(
            gl_points,
            dtype="f4",
        )

        self.vbo = (
            self.ctx.buffer(
                gl_points.tobytes()
            )
        )

        self.vao = (
            self.ctx.vertex_array(
                self.program,
                [
                    (
                        self.vbo,
                        "2f",
                        "in_position",
                    )
                ],
            )
        )

        self.vao.render(
            moderngl.POINTS
        )
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
    def draw_circles(
        self,
        positions,
        radius,
        color,
    ):

        point_size = (
            self.radius_to_pixels(
                radius
            )
        )

        #
        # Only print when radius changes
        #

        if (
            self.last_debug_radius
            != radius
        ):

            self.last_debug_radius = radius

            print(
                "\n=== DRAW CIRCLES ==="
            )

            print(
                "Radius:",
                radius,
            )

            print(
                "Point Size:",
                point_size,
            )

            print(
                "Color:",
                color,
            )

        if hasattr(
            positions,
            "to_numpy",
        ):

            points = positions.to_numpy()

        else:

            points = np.asarray(
                positions,
                dtype="f4",
            )

        if len(points) == 0:
            return

        gl_points = (
            points * 2.0
        ) - 1.0

        gl_points = np.asarray(
            gl_points,
            dtype="f4",
        )

        #
        # Shader uniforms
        #

        self.program[
            "point_size"
        ].value = point_size

        self.program[
            "color"
        ].value = (
            color[0],
            color[1],
            color[2],
        )

        #
        # Debug verify uniform value
        #

        if (
            self.last_debug_radius
            == radius
        ):

            print(
                "Shader point_size:",
                self.program[
                    "point_size"
                ].value,
            )

        self.vbo = self.ctx.buffer(
            gl_points.tobytes()
        )

        self.vao = self.ctx.vertex_array(
            self.program,
            [
                (
                    self.vbo,
                    "2f",
                    "in_position",
                )
            ],
        )

        self.vao.render(
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