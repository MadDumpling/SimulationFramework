from input import InputManager

from core import EventBus

from simulation_manager import (
    SimulationManager,
)

from rendering import (
    TaichiRenderer,
)

from .controls import SimulationUI


class SimulationApplication:

    def __init__(self):

        self.event_bus = EventBus()

        self.renderer = (
            TaichiRenderer()
        )

        self.manager = (
            SimulationManager()
        )

        self.events = self.event_bus

        self.events.subscribe(
            "simulation.load",
            self.manager.load,
        )

        self.events.subscribe(
            "simulation.reset",
            self.manager.reset,
        )

        self.ui = SimulationUI(
            self.manager,
            self.events,
        )

        self.input_manager = (
            InputManager()
        )

    @property
    def running(self):
        return self.renderer.running

    def initialize(self):

        self.manager.load(
            "Bouncing Balls"
        )


        self.ui.build()

    def update(self):

        self.input_manager.update(
            self.renderer.window,
            disable_mouse_camera=False,
        )

        if not self.ui.paused:
            self.manager.step()

    def render(self):

        self.renderer.begin_frame()

        self.renderer.render(
            self.manager.current,
            self.input_manager.camera,
        )

        self.renderer.end_frame()