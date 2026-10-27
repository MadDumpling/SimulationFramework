from registry import create_simulation


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
        self.current = None

    def load(self, simulation_name):
        """
        Load a simulation by name.

        Example:
            manager.load("Bouncing Balls")
        """

        self.current = create_simulation(
            simulation_name
        )

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