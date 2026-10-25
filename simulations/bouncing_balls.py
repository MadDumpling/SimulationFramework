import taichi as ti

from simulations.base import Simulation

N = 500

class BouncingBalls(Simulation):

    def __init__(self):
        self.radius = 0.01

        self.positions = ti.Vector.field(2, ti.f32, shape=N)
        self.velocities = ti.Vector.field(2, ti.f32, shape=N)

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
    def _step(self):
        for i in self.positions:
            self.velocities[i].y -= 9.8 * 0.005
            self.positions[i] += self.velocities[i] * 0.005

            if self.positions[i].y < self.radius:
                self.positions[i].y = self.radius
                self.velocities[i].y *= -0.9

    def step(self):
        self._step()

    def render(self, canvas):
        canvas.circles(
            self.positions,
            radius=self.radius,
            color=(0.2, 0.8, 1.0)
        )