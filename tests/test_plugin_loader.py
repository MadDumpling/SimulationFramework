from plugin_loader import (
    load_simulations
)

from registry import SIMULATIONS


def test_plugin_loading():

    load_simulations()

    assert (
        "Bouncing Balls"
        in SIMULATIONS
    )