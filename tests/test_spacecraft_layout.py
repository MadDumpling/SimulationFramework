import json

import pytest

from core.event_bus import EventBus
from spacecraft.components import Engine, FuelTank, Payload
from spacecraft.presets import load_spacecraft, save_spacecraft
from spacecraft.vehicle import Spacecraft
from ui.spacecraft_designer import SpacecraftDesignerUI
from ui.simulation_application import SimulationApplication
import ui.spacecraft_designer as designer_module


def make_craft():
    craft = Spacecraft("Layout test")
    craft.add_component(
        Engine(name="Engine", dry_mass=10.0, thrust=1_000.0, isp=300.0, fuel_type="test")
    )
    craft.add_component(
        FuelTank(
            name="Tank",
            dry_mass=20.0,
            capacity=100.0,
            fuel_mass=80.0,
            fuel_type="test",
        )
    )
    craft.add_component(Payload(name="Payload", dry_mass=5.0))
    return craft


def test_component_layout_round_trips_in_spacecraft_preset(tmp_path):
    craft = make_craft()
    engine = craft.components[0]
    craft.layout[engine.id] = (0.25, 0.6)
    path = tmp_path / "layout.json"

    save_spacecraft(craft, path)
    restored = load_spacecraft(path)

    assert restored.layout[engine.id] == (0.25, 0.6)
    assert json.loads(path.read_text())["schema_version"] == 2


def test_version_one_preset_loads_with_empty_layout(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "name": "Legacy craft",
                "components": [],
            }
        )
    )

    craft = load_spacecraft(path)

    assert craft.name == "Legacy craft"
    assert craft.layout == {}


def test_select_component_and_move_selected_component_with_wasd():
    craft = make_craft()
    ui = SpacecraftDesignerUI(EventBus(), preset_path="missing-layout-preset.json")
    ui.spacecraft = craft
    ui._ensure_component_layout()
    component = craft.components[0]

    ui.select_component(None, True, component.id)
    start_x, start_y = craft.layout[component.id]
    ui.move_selected_component("w")
    assert craft.layout[component.id] == pytest.approx(
        (start_x, start_y - ui.MOVE_STEP)
    )
    ui.move_selected_component("a")
    assert craft.layout[component.id] == pytest.approx(
        (start_x - ui.MOVE_STEP, start_y - ui.MOVE_STEP)
    )


def test_wasd_move_is_bounded_and_requires_selection():
    ui = SpacecraftDesignerUI(EventBus(), preset_path="missing-layout-preset.json")
    craft = make_craft()
    ui.spacecraft = craft
    ui._ensure_component_layout()

    assert ui.move_selected_component("w") is False
    component = craft.components[0]
    ui.select_component(None, True, component.id)
    craft.layout[component.id] = (ui.LAYOUT_MIN, ui.LAYOUT_MIN)

    for _ in range(100):
        ui.move_selected_component("a")
        ui.move_selected_component("w")

    assert craft.layout[component.id] == (ui.LAYOUT_MIN, ui.LAYOUT_MIN)


def test_keyboard_handler_moves_only_when_selectable_not_text_input_has_focus(
    monkeypatch,
):
    ui = SpacecraftDesignerUI(EventBus(), preset_path="missing-layout-preset.json")
    ui._ensure_component_layout()
    component = ui.spacecraft.components[0]
    ui.selected_component_id = component.id
    selectable_tag = f"spacecraft_component_select_{component.id}"
    focused_tag = {selectable_tag}
    monkeypatch.setattr(designer_module.dpg, "does_item_exist", lambda _tag: True)
    monkeypatch.setattr(
        designer_module.dpg,
        "is_item_focused",
        lambda tag: tag in focused_tag,
    )
    before = ui.spacecraft.layout[component.id]

    ui._handle_movement_key(None, None, "d")
    after_selectable_focus = ui.spacecraft.layout[component.id]

    focused_tag.clear()
    focused_tag.add("spacecraft_name_input")
    ui._handle_movement_key(None, None, "d")

    assert after_selectable_focus[0] == pytest.approx(before[0] + ui.MOVE_STEP)
    assert ui.spacecraft.layout[component.id] == after_selectable_focus


def test_remove_component_also_removes_its_layout():
    craft = make_craft()
    component = craft.components[0]
    craft.layout[component.id] = (0.5, 0.5)

    assert craft.remove_component(component.id) is True
    assert component.id not in craft.layout


def test_default_application_uses_spacecraft_designer_not_demo_simulations():
    application = SimulationApplication()

    assert application.spacecraft_ui.spacecraft.name == "Chemical Explorer Concept"
    assert not hasattr(application, "manager")
    assert not hasattr(application, "renderer")

    application.initialize()

    assert application.spacecraft_ui.built is True
