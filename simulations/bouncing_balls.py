import taichi as ti

from simulations.base import Simulation
from parameters import Parameter

N = 500


@ti.data_oriented
class BouncingBalls(Simulation):

    def __init__(self):

        self.parameters = {
            "gravity": Parameter(
                "Gravity",
                9.8,
                0.0,
                20.0
            ),
            "damping": Parameter(
                "Damping",
                0.9,
                0.0,
                1.0
            ),
            "radius": Parameter(
                "Radius",
                0.01,
                0.001,
                0.05
            )
        }

        self.positions = ti.Vector.field(
            2,
            ti.f32,
            shape=N
        )

        self.velocities = ti.Vector.field(
            2,
            ti.f32,
            shape=N
        )

        self.reset()

    @ti.kernel
    def initialize(self):
        for i in range(N):

            self.positions[i] = [
                ti.random() * 0.8 + 0.1,
                ti.random() * 0.8 + 0.1
            ]

            self.velocities[i] = [
                (ti.random() - 0.5) * 2,
                (ti.random() - 0.5) * 2
            ]

    def reset(self):
        self.initialize()

    @ti.kernel
    def _step(
        self,
        gravity: ti.f32,
        damping: ti.f32
    ):
        for i in self.positions:

            self.velocities[i].y -= gravity * 0.005

            self.positions[i] += (
                self.velocities[i] * 0.005
            )

            if self.positions[i].y < self.parameters["radius"].value:
                self.positions[i].y = self.parameters["radius"].value
                self.velocities[i].y *= -damping

    def step(self):

        gravity = self.parameters["gravity"].value
        damping = self.parameters["damping"].value

        self._step(
            gravity,
            damping
        )

    def render(self, canvas):

        radius = self.parameters["radius"].value

        canvas.circles(
            self.positions,
            radius=radius,
            color=(0.2, 0.8, 1.0)
        )