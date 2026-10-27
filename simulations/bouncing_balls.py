# bouncing_balls.py
import taichi as ti

from registry import register_simulation
from simulations.base import Simulation
from parameters import Parameter

N = 500


@register_simulation
@ti.data_oriented
class BouncingBalls(Simulation):

    name = "Bouncing Balls"
    author = "You"
    version = "0.1"

    def __init__(self):
        super().__init__()

        self.parameters = {
            "gravity": Parameter(
                "Gravity",
                9.8,
                0.0,
                20.0,
            ),
            "damping": Parameter(
                "Damping",
                0.9,
                0.0,
                1.0,
            ),
            "radius": Parameter(
                "Radius",
                0.01,
                0.001,
                0.05,
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
                ti.random() * 0.8 + 0.1,
                ti.random() * 0.8 + 0.1,
            ]

            self.velocities[i] = [
                (ti.random() - 0.5) * 2.0,
                (ti.random() - 0.5) * 2.0,
            ]

    def reset(self):
        self.initialize()

    @ti.kernel
    def _step(
        self,
        gravity: ti.f32,
        damping: ti.f32,
        radius: ti.f32,
    ):
        for i in self.positions:

            self.velocities[i].y -= gravity * 0.005

            self.positions[i] += (
                self.velocities[i] * 0.005
            )

            if self.positions[i].y < radius:
                self.positions[i].y = radius
                self.velocities[i].y *= -damping

    def step(self):

        gravity = self.parameters["gravity"].value
        damping = self.parameters["damping"].value
        radius = self.parameters["radius"].value

        self._step(
            gravity,
            damping,
            radius,
        )

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
                p -
                ti.Vector([offset_x, offset_y])
            ) * zoom

            p += ti.Vector([0.5, 0.5])

            self.render_positions[i] = p

    def render(self, canvas, camera):

        self.update_render_positions(
            camera.offset[0],
            camera.offset[1],
            camera.zoom,
        )

        canvas.circles(
            self.render_positions,
            radius=(
                self.parameters["radius"].value *
                camera.zoom
            ),
            color=(0.2, 0.8, 1.0),
        )
