from registry import create_simulation
from core.serialization import (
    save_preset,
    load_preset,
)
from registry import (
    create_simulation,
    get_simulation_names,
)
class SimulationManager:
    """
    Manages the currently active simulation.

    Responsibilities:
    - Load simulations
    - Hold the current simulation
    - Forward update/render calls

    Future:
    - Hot reloading
    - Serialization
    - Time travel
    - Simulation switching UI
    """

    def __init__(self):

        self.instances = {}
        for name in get_simulation_names():
            self.instances[name] = (
                create_simulation(name)
                )
        self.current = None
    def load(self, simulation_name):
        """
        Load a simulation by name.

        Example:
            manager.load("Bouncing Balls")
        """

        self.current = self.instances[
            simulation_name
        ]

    def reset(self):
        """
        Reset the current simulation.
        """

        if self.current:
            self.current.reset()

    def step(self):
        """
        Advance the current simulation.
        """

        if self.current:
            self.current.step()

    def render(self, canvas, camera):
        """
        Render the current simulation.
        """

        if self.current:
            self.current.render(
                canvas,
                camera,
            )
    def save_preset(
        self,
        filepath,
    ):

        if self.current:

            save_preset(
                self.current,
                filepath,
            )


    def load_preset(
        self,
        filepath,
    ):

        if self.current:

            load_preset(
                self.current,
                filepath,
            )