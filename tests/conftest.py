import sys
import unittest.mock
from pathlib import Path

# Mock DearPyGui so UI code can be imported without a display (headless CI).
m = unittest.mock.MagicMock()
m.does_item_exist.return_value = True
sys.modules['dearpygui'] = m
sys.modules['dearpygui.dearpygui'] = m

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
