import dearpygui.dearpygui as dpg
import moderngl
import numpy as np

from .renderer import Renderer


MESH_VERTEX_SHADER = """
#version 330

in vec3 in_position;
in vec3 in_normal;

uniform mat4 view_projection;
uniform mat4 model;
uniform mat3 normal_matrix;

out vec3 world_position;
out vec3 world_normal;

void main()
{
    vec4 world = model * vec4(in_position, 1.0);
    world_position = world.xyz;
    world_normal = normal_matrix * in_normal;
    gl_Position = view_projection * world;
}
"""


MESH_FRAGMENT_SHADER = """
#version 330

in vec3 world_position;
in vec3 world_normal;

uniform vec3 color;
uniform vec3 eye;
uniform float highlight;

out vec4 fragColor;

const vec3 KEY_LIGHT = normalize(vec3(0.55, 0.75, 0.35));
const vec3 FILL_LIGHT = normalize(vec3(-0.6, 0.2, -0.5));
const vec3 HIGHLIGHT_COLOR = vec3(1.0, 0.62, 0.15);

void main()
{
    vec3 view_dir = normalize(eye - world_position);
    vec3 normal = normalize(world_normal);
    // Two-sided lighting so open shapes such as nozzle bells shade inside.
    if (dot(normal, view_dir) < 0.0)
    {
        normal = -normal;
    }

    float key = max(dot(normal, KEY_LIGHT), 0.0);
    float fill = max(dot(normal, FILL_LIGHT), 0.0) * 0.25;
    vec3 half_dir = normalize(KEY_LIGHT + view_dir);
    float specular = pow(max(dot(normal, half_dir), 0.0), 48.0) * 0.35;
    float rim = pow(1.0 - max(dot(normal, view_dir), 0.0), 3.0);

    vec3 lit = color * (0.16 + key * 0.9 + fill)
        + vec3(specular)
        + rim * vec3(0.25, 0.35, 0.55) * 0.5;
    lit = mix(lit, HIGHLIGHT_COLOR, highlight * (0.25 + 0.6 * rim));
    fragColor = vec4(lit, 1.0);
}
"""


PICK_FRAGMENT_SHADER = """
#version 330

in vec3 world_position;
in vec3 world_normal;

uniform vec3 pick_color;
out vec4 fragColor;

void main()
{
    fragColor = vec4(pick_color, 1.0);
}
"""


LINE_VERTEX_SHADER = """
#version 330

in vec3 in_position;
uniform mat4 view_projection;

void main()
{
    gl_Position = view_projection * vec4(in_position, 1.0);
}
"""


LINE_FRAGMENT_SHADER = """
#version 330

uniform vec4 color;
out vec4 fragColor;

void main()
{
    fragColor = color;
}
"""


def _gl_matrix(matrix):
    """Pack a row-major numpy matrix as column-major float32 bytes for GLSL."""
    return np.ascontiguousarray(
        np.asarray(matrix, dtype=np.float32).T
    ).tobytes()


def encode_pick_id(pick_id):
    return (
        (pick_id & 0xFF) / 255.0,
        ((pick_id >> 8) & 0xFF) / 255.0,
        ((pick_id >> 16) & 0xFF) / 255.0,
    )


def decode_pick_id(rgb):
    return int(rgb[0]) | (int(rgb[1]) << 8) | (int(rgb[2]) << 16)


class OpenGLRenderer(Renderer):
    def __init__(self):
        self.width = 1280
        self.height = 720
        self.ctx = moderngl.create_standalone_context()
        self.texture = self.ctx.texture(
            (self.width, self.height),
            4,
            dtype="f1",
        )
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.texture],
            depth_attachment=self.ctx.depth_renderbuffer(
                (self.width, self.height),
            ),
        )
        self.msaa_fbo = self._create_msaa_framebuffer(samples=4)
        self.render_fbo = self.msaa_fbo or self.fbo

        self.mesh_program = self.ctx.program(
            vertex_shader=MESH_VERTEX_SHADER,
            fragment_shader=MESH_FRAGMENT_SHADER,
        )
        self.pick_program = self.ctx.program(
            vertex_shader=MESH_VERTEX_SHADER,
            fragment_shader=PICK_FRAGMENT_SHADER,
        )
        self.line_program = self.ctx.program(
            vertex_shader=LINE_VERTEX_SHADER,
            fragment_shader=LINE_FRAGMENT_SHADER,
        )
        self.pick_fbo = self.ctx.framebuffer(
            color_attachments=[
                self.ctx.texture((self.width, self.height), 4, dtype="f1"),
            ],
            depth_attachment=self.ctx.depth_renderbuffer(
                (self.width, self.height),
            ),
        )
        self._meshes = {}
        self._pick_draws = []
        self._line_vbo = None
        self._line_vao = None
        self._line_capacity = 0

        self._frame_upload = np.empty(
            (self.height, self.width, 4),
            dtype=np.float32,
        )

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

    @property
    def aspect(self):
        return self.width / self.height

    def _create_msaa_framebuffer(self, samples):
        samples = min(samples, self.ctx.max_samples)
        if samples < 2:
            return None
        try:
            return self.ctx.framebuffer(
                color_attachments=[
                    self.ctx.renderbuffer(
                        (self.width, self.height),
                        4,
                        samples=samples,
                    )
                ],
                depth_attachment=self.ctx.depth_renderbuffer(
                    (self.width, self.height),
                    samples=samples,
                ),
            )
        except moderngl.Error:
            return None

    def begin_frame(self):
        self.render_fbo.use()
        self.ctx.clear(0.03, 0.035, 0.06, 1.0, depth=1.0)
        self._pick_draws.clear()

    def set_camera(self, view_projection, eye):
        packed = _gl_matrix(view_projection)
        self.mesh_program["view_projection"].write(packed)
        self.pick_program["view_projection"].write(packed)
        self.line_program["view_projection"].write(packed)
        self.mesh_program["eye"].value = tuple(float(v) for v in eye)

    def _mesh_vaos(self, key, mesh):
        cached = self._meshes.get(key)
        if cached is None:
            vbo = self.ctx.buffer(mesh.interleaved().tobytes())
            cached = (
                self.ctx.vertex_array(
                    self.mesh_program,
                    [(vbo, "3f 3f", "in_position", "in_normal")],
                ),
                self.ctx.vertex_array(
                    self.pick_program,
                    [(vbo, "3f 12x", "in_position")],
                ),
                vbo,
            )
            self._meshes[key] = cached
        return cached

    def draw_mesh(
        self,
        key,
        mesh,
        model,
        color,
        highlight=0.0,
        pick_id=0,
    ):
        """Draw a lit triangle mesh; GPU buffers are cached per ``key``."""
        vao, _, _ = self._mesh_vaos(key, mesh)
        model = np.asarray(model, dtype=np.float32)
        normal_matrix = np.linalg.inv(model[:3, :3]).T
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.mesh_program["model"].write(_gl_matrix(model))
        self.mesh_program["normal_matrix"].write(_gl_matrix(normal_matrix))
        self.mesh_program["color"].value = tuple(color[:3])
        self.mesh_program["highlight"].value = float(highlight)
        vao.render(moderngl.TRIANGLES)
        if pick_id:
            self._pick_draws.append((key, model, pick_id))

    def draw_lines_3d(self, points, color):
        """Draw world-space line segments from an (N*2, 3) array."""
        points = np.ascontiguousarray(points, dtype=np.float32)
        if points.size == 0:
            return
        count = len(points)
        if count > self._line_capacity:
            if self._line_vao is not None:
                self._line_vao.release()
                self._line_vbo.release()
            self._line_capacity = max(count, 1024)
            self._line_vbo = self.ctx.buffer(
                reserve=self._line_capacity * 12,
            )
            self._line_vao = self.ctx.vertex_array(
                self.line_program,
                [(self._line_vbo, "3f", "in_position")],
            )
        self._line_vbo.write(points.tobytes())
        self.line_program["color"].value = (
            tuple(color) + (1.0,) * (4 - len(color))
        )
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.BLEND)
        self.ctx.blend_func = (
            moderngl.SRC_ALPHA,
            moderngl.ONE_MINUS_SRC_ALPHA,
        )
        self._line_vao.render(moderngl.LINES, vertices=count)
        self.ctx.disable(moderngl.BLEND)

    def pick(self, x, y):
        """Return the pick id at normalized viewport coords (origin bottom-left).

        Replays this frame's pickable draws into an offscreen ID buffer, so it
        costs nothing unless called. Returns 0 for background.
        """
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            return 0
        px = min(int(x * self.width), self.width - 1)
        py = min(int(y * self.height), self.height - 1)

        self.pick_fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0, depth=1.0)
        self.ctx.enable(moderngl.DEPTH_TEST)
        for key, model, pick_id in self._pick_draws:
            pick_vao = self._meshes[key][1]
            self.pick_program["model"].write(_gl_matrix(model))
            self.pick_program["pick_color"].value = encode_pick_id(pick_id)
            pick_vao.render(moderngl.TRIANGLES)
        rgb = self.pick_fbo.read(viewport=(px, py, 1, 1), components=3)
        self.render_fbo.use()
        return decode_pick_id(rgb)

    def end_frame(self):
        msaa_fbo = getattr(self, "msaa_fbo", None)
        if msaa_fbo is not None:
            self.ctx.copy_framebuffer(self.fbo, msaa_fbo)

        pixels = np.frombuffer(self.texture.read(), dtype=np.uint8)
        pixels = pixels.reshape((self.height, self.width, 4))

        # Convert and flip in one pass into a contiguous reusable upload buffer.
        np.multiply(pixels[::-1], 1.0 / 255.0, out=self._frame_upload)

        if dpg.does_item_exist("viewport_texture"):
            dpg.set_value(
                "viewport_texture",
                self._frame_upload.reshape(-1),
            )
