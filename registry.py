# registry.py

"""
Simulation Registry

Purpose
-------
The registry keeps track of every simulation available to the framework.

Instead of manually adding simulations to a list, simulations register
themselves automatically using the @register_simulation decorator.

Example
-------

@register_simulation
class BouncingBalls(Simulation):
    name = "Bouncing Balls"

After the module is imported:

SIMULATIONS == {
    "Bouncing Balls": BouncingBalls
}

This allows the framework to:

- Automatically discover simulations
- Populate simulation dropdowns
- Create simulation instances dynamically
- Support plugin loading
- Support hot reloading
"""

# Dictionary storing all registered simulations.
#
# Format:
#
# {
#     "Simulation Name": SimulationClass
# }
#
SIMULATIONS = {}

def create_simulation(name):
    return SIMULATIONS[name]()

def register_simulation(cls):
    """
    Register a simulation class with the framework.

    This decorator should be placed above every simulation class.

    Example
    -------

    @register_simulation
    class Boids(Simulation):
        name = "Boids"

    What happens
    ------------

    Before:

        SIMULATIONS = {}

    After importing the file:

        SIMULATIONS = {
            "Boids": Boids
        }

    Parameters
    ----------
    cls : type
        Simulation class to register.

    Returns
    -------
    type
        Returns the original class unchanged.
        This is required for decorators to work correctly.
    """

    # Use the simulation's name as the registry key.
    #
    # Example:
    #
    # "Boids" -> Boids
    # "Fluid" -> FluidSimulation
    #
    SIMULATIONS[cls.name] = cls

    return cls


def get_simulation(name):
    """
    Retrieve a simulation class by name.

    Example
    -------

    sim_class = get_simulation("Boids")
    sim = sim_class()

    Parameters
    ----------
    name : str
        Name of the simulation.

    Returns
    -------
    type | None
        The registered simulation class,
        or None if it does not exist.
    """

    return SIMULATIONS.get(name)


def get_simulation_names():
    """
    Return all registered simulation names.

    Useful for UI dropdowns.

    Example
    -------

    dpg.add_combo(
        get_simulation_names()
    )

    Returns
    -------
    list[str]
        Sorted list of simulation names.
    """

    return sorted(SIMULATIONS.keys())