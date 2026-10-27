import taichi as ti

from registry import register_simulation
from simulations.base import Simulation
from parameters import Parameter


N = 300


@register_simulation
@ti.data_oriented
class Boids(Simulation):

    name = "Boids"
    author = "You"
    version = "0.3"

    def __init__(self):

        super().__init__()

        self.parameters = {
            "cohesion": Parameter(
                "Cohesion",
                0.5,
                0.0,
                2.0,
            ),
            "alignment": Parameter(
                "Alignment",
                0.5,
                0.0,
                2.0,
            ),
            "separation": Parameter(
                "Separation",
                1.0,
                0.0,
                3.0,
            ),
            "speed": Parameter(
                "Speed",
                0.5,
                0.1,
                3.0,
            ),
            "radius": Parameter(
                "Radius",
                0.005,
                0.001,
                0.02,
            ),
        }

        self.positions = ti.Vector.field(
            2,
            ti.f32,
            shape=N,
        )

        self.velocities = ti.Vector.field(
            2,
            ti.f32,
            shape=N,
        )

        self.render_positions = ti.Vector.field(
            2,
            ti.f32,
            shape=N,
        )

        self.reset()

    @ti.kernel
    def initialize(self):

        for i in range(N):

            self.positions[i] = [
                ti.random(),
                ti.random(),
            ]

            angle = (
                ti.random()
                * 6.28318
            )

            self.velocities[i] = [
                ti.cos(angle),
                ti.sin(angle),
            ]

    def reset(self):
        self.initialize()

    @ti.kernel
    def _step(
        self,
        speed: ti.f32,
    ):

        for i in self.positions:

            self.positions[i] += (
                self.velocities[i]
                * speed
                * 0.002
            )

            if self.positions[i].x < 0.0:
                self.positions[i].x += 1.0

            if self.positions[i].x > 1.0:
                self.positions[i].x -= 1.0

            if self.positions[i].y < 0.0:
                self.positions[i].y += 1.0

            if self.positions[i].y > 1.0:
                self.positions[i].y -= 1.0

    def step(self):

        speed = (
            self.parameters["speed"]
            .value
        )

        self._step(speed)

    @ti.kernel
    def update_render_positions(
        self,
        offset_x: ti.f32,
        offset_y: ti.f32,
        zoom: ti.f32,
    ):

        for i in self.positions:

            p = self.positions[i]

            p = (
                p
                - ti.Vector(
                    [offset_x, offset_y]
                )
            ) * zoom

            p += ti.Vector(
                [0.5, 0.5]
            )

            self.render_positions[i] = p

    def render(
        self,
        canvas,
        camera,
    ):

        self.update_render_positions(
            camera.offset[0],
            camera.offset[1],
            camera.zoom,
        )

        canvas.circles(
            self.render_positions,
            radius=self.parameters[
                "radius"
            ].value
            * camera.zoom,
            color=(1.0, 0.8, 0.2),
        )