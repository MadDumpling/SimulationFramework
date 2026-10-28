import sys
import unittest.mock
from pathlib import Path

import pytest

# 🟢 CREATE A SAFE VIRTUAL ENGINE MOCK TO PREVENT HEADLESS CI SEGFUALTS
m = unittest.mock.MagicMock()
m.does_item_exist.return_value = True
sys.modules['dearpygui'] = m
sys.modules['dearpygui.dearpygui'] = m

# =========================================================================
# ORIGINAL ENVIRONMENT INITIALIZATION ACTIONS
# =========================================================================
import taichi as ti

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session", autouse=True)
def initialize_taichi():
    """
    Initialize Taichi once before any tests run.

    Many simulations create Taichi fields in their
    constructors, which requires ti.init() to have
    already been called.
    """
    ti.init(
        arch=ti.cpu,
        offline_cache=False,
    )
