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
        damping: ti.f32,
        radius: ti.f32
    ):
        # 1. Apply Gravity, Movement, and Wall Collisions
        for i in self.positions:
            self.velocities[i].y -= gravity * 0.005
            self.positions[i] += self.velocities[i] * 0.005

            # Floor Collision
            if self.positions[i].y < radius:
                self.positions[i].y = radius
                self.velocities[i].y *= -damping

            # Ceiling Collision
            if self.positions[i].y > 1.0 - radius:
                self.positions[i].y = 1.0 - radius
                self.velocities[i].y *= -damping

            # Left Wall Collision
            if self.positions[i].x < radius:
                self.positions[i].x = radius
                self.velocities[i].x *= -damping

            # Right Wall Collision
            if self.positions[i].x > 1.0 - radius:
                self.positions[i].x = 1.0 - radius
                self.velocities[i].x *= -damping

        # 2. Handle Ball-to-Ball Collisions
        for i in self.positions:
            for j in range(N):
                if i != j:
                    pos_diff = self.positions[i] - self.positions[j]
                    dist = pos_diff.norm()
                    min_dist = 2.0 * radius

                    if dist < min_dist:
                        if dist == 0.0:
                            continue
                        
                        normal = pos_diff / dist
                        overlap = min_dist - dist
                        
                        # Separate the overlapping balls
                        self.positions[i] += normal * overlap * 0.5

                        # Calculate kinetic energy transfer (Elastic Collision)
                        vel_diff = self.velocities[i] - self.velocities[j]
                        vel_along_normal = vel_diff.dot(normal)

                        if vel_along_normal < 0.0:
                            impulse = vel_along_normal
                            self.velocities[i] -= normal * impulse * damping
                            self.velocities[j] += normal * impulse * damping

    def step(self):
        gravity = self.parameters["gravity"].value
        damping = self.parameters["damping"].value
        radius = self.parameters["radius"].value

        self._step(
            gravity,
            damping,
            radius
        )

    def render(self, canvas):

        radius = self.parameters["radius"].value

        canvas.circles(
            self.positions,
            radius=radius,
            color=(0.2, 0.8, 1.0)
        )
