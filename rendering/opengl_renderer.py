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
    gl_Position = vec4(in_position, 0.0, 1.0);
    gl_PointSize = point_size;
}
"""


FRAGMENT_SHADER = """
#version 330

uniform vec3 color;
out vec4 fragColor;

void main()
{
    vec2 uv = gl_PointCoord - vec2(0.5);
    if (length(uv) > 0.5)
    {
        discard;
    }
    fragColor = vec4(color, 1.0);
}
"""


class OpenGLRenderer(Renderer):
    def __init__(self):
        self.width = 1280
        self.height = 720
        self.ctx = moderngl.create_standalone_context()
        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER,
        )
        self.program["point_size"].value = 30.0
        self.program["color"].value = (1.0, 1.0, 1.0)
        self.texture = self.ctx.texture(
            (self.width, self.height),
            4,
            dtype="f1",
        )
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.texture],
        )

        self._point_capacity = 0
        self._gl_points = np.empty((0, 2), dtype=np.float32)
        self.vbo = None
        self.vao = None
        self._frame_upload = np.empty(
            (self.height, self.width, 4),
            dtype=np.float32,
        )

        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.last_debug_radius = None

        print("OpenGL initialized")
        print("Renderer:", self.ctx.info.get("GL_RENDERER"))
        print("Vendor:", self.ctx.info.get("GL_VENDOR"))
        print("Version:", self.ctx.info.get("GL_VERSION"))

    @property
    def name(self):
        return "OpenGL"

    @property
    def running(self):
        return True

    def begin_frame(self):
        self.fbo.use()
        self.ctx.clear(0.05, 0.05, 0.08, 1.0)

    def clear(self, color):
        self.ctx.clear(color[0], color[1], color[2], 1.0)

    def _ensure_point_capacity(self, count):
        if count <= self._point_capacity:
            return

        self._point_capacity = max(
            count,
            max(1024, self._point_capacity * 2),
        )
        self._gl_points = np.empty(
            (self._point_capacity, 2),
            dtype=np.float32,
        )

        if self.vao is not None:
            self.vao.release()
        if self.vbo is not None:
            self.vbo.release()

        byte_capacity = self._point_capacity * 2 * np.dtype(np.float32).itemsize
        self.vbo = self.ctx.buffer(reserve=byte_capacity)
        self.vao = self.ctx.vertex_array(
            self.program,
            [(self.vbo, "2f", "in_position")],
        )

    def _draw_positions(self, positions, color):
        points = (
            positions.to_numpy()
            if hasattr(positions, "to_numpy")
            else np.asarray(positions)
        )
        if points.size == 0:
            return

        count = len(points)
        self._ensure_point_capacity(count)
        gl_points = self._gl_points[:count]

        # Transform into reusable staging memory instead of allocating two arrays.
        np.multiply(points, 2.0, out=gl_points)
        np.subtract(gl_points, 1.0, out=gl_points)
        self.vbo.write(memoryview(gl_points).cast("B"))
        self.program["color"].value = tuple(color[:3])
        self.vao.render(moderngl.POINTS, vertices=count)

    def draw_points(self, positions, color):
        self._draw_positions(positions, color)

    def radius_to_pixels(self, radius):
        return max(
            1.0,
            radius * min(self.width, self.height) * 2.0,
        )

    def draw_circles(self, positions, radius, color):
        point_size = self.radius_to_pixels(radius)
        if self.last_debug_radius != radius:
            self.last_debug_radius = radius
            print("Radius:", radius, "Point Size:", point_size, "Color:", color)

        self.program["point_size"].value = point_size
        self._draw_positions(positions, color)

    def draw_lines(self, start, end, color):
        pass

    def end_frame(self):
        pixels = np.frombuffer(self.texture.read(), dtype=np.uint8)
        pixels = pixels.reshape((self.height, self.width, 4))

        # Convert and flip in one pass into a contiguous reusable upload buffer.
        np.multiply(pixels[::-1], 1.0 / 255.0, out=self._frame_upload)

        if dpg.does_item_exist("viewport_texture"):
            dpg.set_value(
                "viewport_texture",
                self._frame_upload.reshape(-1),
            )