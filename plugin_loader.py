# plugin_loader.py

import importlib
import pathlib


def load_simulations():
    """
    Discover and import every simulation module.

    Importing a module causes its
    @register_simulation decorator
    to execute automatically.
    """

    simulation_dir = pathlib.Path("simulations")

    for file in simulation_dir.glob("*.py"):

        # Skip internal files
        if file.stem.startswith("_"):
            continue

        # Skip abstract base class
        if file.stem == "base":
            continue

        module_name = f"simulations.{file.stem}"

        print(f"Loading {module_name}")

        importlib.import_module(module_name)