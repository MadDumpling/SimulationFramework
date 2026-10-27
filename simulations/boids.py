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
            "separation": Parameter(
                "Separation",
                1.5,
                0.0,
                5.0,
            ),
            "alignment": Parameter(
                "Alignment",
                1.0,
                0.0,
                5.0,
            ),
            "cohesion": Parameter(
                "Cohesion",
                1.0,
                0.0,
                5.0,
            ),
            "neighbor_radius": Parameter(
                "Neighbor Radius",
                0.08,
                0.01,
                0.2,
            ),
            "max_speed": Parameter(
                "Max Speed",
                1.0,
                0.1,
                5.0,
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
        separation_strength: ti.f32,
        alignment_strength: ti.f32,
        cohesion_strength: ti.f32,
        neighbor_radius: ti.f32,
        max_speed: ti.f32,
    ):

        for i in range(N):

            separation = ti.Vector([
                0.0,
                0.0,
            ])

            alignment = ti.Vector([
                0.0,
                0.0,
            ])

            cohesion = ti.Vector([
                0.0,
                0.0,
            ])

            count = 0

            for j in range(N):

                if i == j:
                    continue

                diff = (
                    self.positions[j]
                    - self.positions[i]
                )

                dist = diff.norm()

                if (
                    dist > 0.0
                    and
                    dist < neighbor_radius
                ):

                    count += 1

                    alignment += (
                        self.velocities[j]
                    )

                    cohesion += (
                        self.positions[j]
                    )

                    separation -= (
                        diff
                        /
                        (dist + 0.001)
                    )

            if count > 0:

                alignment /= count
                cohesion /= count

                cohesion -= (
                    self.positions[i]
                )

                self.velocities[i] += (
                    separation
                    * separation_strength
                    * 0.01
                )

                self.velocities[i] += (
                    alignment
                    * alignment_strength
                    * 0.01
                )

                self.velocities[i] += (
                    cohesion
                    * cohesion_strength
                    * 0.01
                )

            speed = (
                self.velocities[i]
                .norm()
            )

            if speed > max_speed:

                self.velocities[i] = (
                    self.velocities[i]
                    /
                    speed
                    * max_speed
                )

            self.positions[i] += (
                self.velocities[i]
                * 0.005
            )

            if self.positions[i].x < 0:
                self.positions[i].x += 1

            if self.positions[i].x > 1:
                self.positions[i].x -= 1

            if self.positions[i].y < 0:
                self.positions[i].y += 1

            if self.positions[i].y > 1:
                self.positions[i].y -= 1

    def step(self):

        self._step(
            self.parameters[
                "separation"
            ].value,

            self.parameters[
                "alignment"
            ].value,

            self.parameters[
                "cohesion"
            ].value,

            self.parameters[
                "neighbor_radius"
            ].value,

            self.parameters[
                "max_speed"
            ].value,
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