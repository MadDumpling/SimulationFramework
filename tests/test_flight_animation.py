import threading
import time
import types

import numpy as np
import pytest

from core.event_bus import EventBus
from rendering import OpenGLRenderer
from spacecraft.geometry import rotation_between
from spacecraft.presets import load_spacecraft
from spacecraft.appearance import SpacecraftAppearance
from spacecraft.vehicle import Spacecraft
from ui.spacecraft_designer import DEFAULT_PRESET, SpacecraftDesignerUI
import ui.spacecraft_designer as designer_module
from viewport import SpacecraftViewport
from viewport import flight as f
from viewport.flight import FlightAnimation

Y = np.array([0.0, 1.0, 0.0])


def run(animation, seconds, dt=1 / 60):
    for _ in range(int(seconds / dt)):
        animation.update(dt)


def launched(height=10.0, **kwargs):
    animation = FlightAnimation()
    animation.launch(center=(0.0, height / 2.0, 0.0), height=height, core_radius=1.0, **kwargs)
    return animation


def hovering(height=10.0):
    animation = launched(height)
    run(animation, 15.0)
    return animation


def vehicle_axis(animation):
    return animation.orientation[:3, :3] @ Y


# -- ascent -------------------------------------------------------------------


def test_idle_until_launched_and_hides_moon():
    animation = FlightAnimation()

    assert animation.state == f.IDLE
    assert not animation.active and not animation.moon_visible
    np.testing.assert_allclose(animation.vehicle_matrix(), np.eye(4), atol=1e-6)


def test_launch_climbs_then_hovers_with_engine_burning():
    animation = launched()
    run(animation, 1.0)
    early = animation.position[1]
    run(animation, 40.0)

    assert animation.state == f.ASCENDING
    assert animation.burning and animation.moon_visible
    assert early > 5.0
    hover = 5.0 + f.HOVER_HEIGHT * 10.0
    assert animation.position[1] == pytest.approx(hover, rel=0.02)
    assert animation.position[1] <= hover + 1e-6  # never overshoots the hover point


def test_unknown_outcome_is_rejected():
    with pytest.raises(ValueError):
        launched().conclude("success")


def test_conclude_only_applies_while_ascending():
    idle = FlightAnimation()
    idle.conclude(f.LAND)
    assert idle.state == f.IDLE

    animation = hovering()
    animation.conclude(f.FALL)
    animation.conclude(f.LAND)  # a second verdict cannot change the first
    assert animation.state == f.FALLING


# -- success: soft landing on the Moon ---------------------------------------


def test_successful_mission_lands_softly_standing_on_the_moon():
    animation = hovering()
    animation.conclude(f.LAND)
    assert animation.state == f.DESCENDING and animation.burning

    run(animation, f.LAND_TIME + 1.0)

    assert animation.state == f.LANDED
    assert animation.vehicle_visible and not animation.burning
    assert animation.flash() is None  # a landing, not a crash
    # Base on the surface: the centre sits half a vehicle height above it.
    radial = animation.position - animation.moon_center
    assert np.linalg.norm(radial) == pytest.approx(
        animation.moon_radius + 0.5 * animation.height, rel=1e-3
    )
    # Standing upright relative to the surface (nose away from the Moon).
    normal = radial / np.linalg.norm(radial)
    np.testing.assert_allclose(vehicle_axis(animation), normal, atol=1e-3)
    assert animation.finished


def test_descent_comes_to_rest_and_never_enters_the_moon():
    animation = hovering()
    animation.conclude(f.LAND)
    previous = animation.position.copy()
    speeds = []
    floor = animation.moon_radius + 0.5 * animation.height
    for _ in range(int((f.LAND_TIME + 1.0) * 60)):
        animation.update(1 / 60)
        gap = np.linalg.norm(animation.position - animation.moon_center)
        assert gap >= floor * 0.999
        speeds.append(np.linalg.norm(animation.position - previous) * 60)
        previous = animation.position.copy()

    assert max(speeds) < 6.0 * animation.height  # no teleporting
    assert speeds[-1] < 0.05 * max(speeds)  # touchdown at (near) rest


def test_vehicle_flips_engine_toward_the_moon_for_the_retro_burn():
    animation = hovering()
    animation.conclude(f.LAND)
    start_axis = vehicle_axis(animation)
    run(animation, f.LAND_TIME + 0.5)

    to_moon = animation.moon_center - animation.position
    to_moon /= np.linalg.norm(to_moon)
    assert np.dot(start_axis, Y) == pytest.approx(1.0, abs=1e-3)
    # Engine (the vehicle base, -axis) points at the surface it is landing on.
    assert np.dot(-vehicle_axis(animation), to_moon) > 0.99


# -- failure: misses the Moon -------------------------------------------------


def test_miss_flies_past_the_moon_and_is_lost_in_space():
    animation = hovering()
    animation.conclude(f.MISS)
    assert animation.state == f.FLYBY and animation.burning

    gaps = []
    for _ in range(int((f.FLYBY_TIME + f.FLYBY_COAST + 1.0) * 60)):
        animation.update(1 / 60)
        gaps.append(np.linalg.norm(animation.position - animation.moon_center))

    assert min(gaps) >= animation.moon_radius * 1.05  # passes by, never touches it
    assert min(gaps) < animation.moon_radius * 2.2  # but does come close
    assert animation.state == f.LOST
    assert not animation.vehicle_visible
    assert animation.finished
    assert gaps[-1] > min(gaps)  # moving away


def test_miss_never_lands_or_crashes():
    animation = hovering()
    animation.conclude(f.MISS)
    seen = set()
    for _ in range(60 * 12):
        animation.update(1 / 60)
        seen.add(animation.state)

    assert seen == {f.FLYBY, f.LOST}
    assert animation.flash() is None


# -- failure: cannot reach the Moon ------------------------------------------


def test_fall_sputters_out_then_crashes_on_the_ground():
    animation = hovering()
    peak = animation.position[1]
    animation.conclude(f.FALL)

    assert animation.state == f.FALLING
    flames = []
    for _ in range(60 * 2):
        animation.update(1 / 60)
        flames.append(animation.burning)
    assert any(flames[:30]) and not any(flames[-30:])  # engine fails, not instantly off

    run(animation, 30.0)

    assert animation.state == f.CRASHED
    assert animation.vehicle_visible and animation.finished
    assert animation.tilt == pytest.approx(np.pi / 2.0)
    assert animation.position[1] == pytest.approx(animation.core_radius, abs=1e-3)
    assert animation.position[1] < peak
    assert animation.flash_center is not None


def test_fall_never_goes_through_the_ground():
    animation = hovering()
    animation.conclude(f.FALL)
    for _ in range(60 * 30):
        animation.update(1 / 60)
        assert animation.position[1] >= animation.core_radius - 1e-6


# -- failure: cannot lift off ------------------------------------------------


def test_no_liftoff_vehicle_never_leaves_the_pad():
    animation = launched(liftoff=False, has_thrust=True)

    assert animation.state == f.NO_LIFTOFF and not animation.moon_visible
    highest = 0.0
    for _ in range(60 * 6):
        animation.update(1 / 60)
        highest = max(highest, animation.position[1] - animation.pivot[1])

    assert highest < 0.02 * animation.height  # shudders, does not fly
    assert animation.position[1] == pytest.approx(animation.pivot[1])
    assert not animation.burning and animation.finished
    animation.conclude(f.LAND)  # a later verdict cannot make it fly
    assert animation.state == f.NO_LIFTOFF


def test_no_liftoff_without_thrust_has_no_flame_and_no_motion():
    animation = launched(liftoff=False, has_thrust=False)
    for _ in range(60):
        animation.update(1 / 60)
        assert not animation.burning
        assert animation.position[1] == pytest.approx(animation.pivot[1])


# -- general ------------------------------------------------------------------


def test_relaunch_restarts_from_the_pad():
    animation = hovering()
    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)

    np.testing.assert_allclose(animation.position, (0.0, 5.0, 0.0))
    assert animation.state == f.ASCENDING and animation.time == 0.0


def test_animation_scales_with_vehicle_height():
    small, large = launched(5.0), launched(50.0)

    assert np.linalg.norm(large.moon_center) == pytest.approx(
        10.0 * np.linalg.norm(small.moon_center)
    )
    assert large.moon_radius == pytest.approx(10.0 * small.moon_radius)


def test_large_frame_time_is_clamped():
    animation = launched()
    animation.update(5.0)

    assert animation.position[1] < 5.0 + 1.0


def test_rotation_between_aligns_directions_and_supports_partial_turns():
    for target in ((1, 0, 0), (0, -1, 0), (0, 1, 0), (1, 2, -3)):
        matrix = rotation_between((0, 1, 0), target)
        moved = matrix[:3, :3] @ Y
        np.testing.assert_allclose(moved, np.array(target) / np.linalg.norm(target), atol=1e-6)
        np.testing.assert_allclose(matrix[:3, :3] @ matrix[:3, :3].T, np.eye(3), atol=1e-6)

    half = rotation_between((0, 1, 0), (1, 0, 0), 0.5)[:3, :3] @ Y
    np.testing.assert_allclose(half, (np.sqrt(0.5), np.sqrt(0.5), 0.0), atol=1e-6)
    np.testing.assert_allclose(rotation_between((0, 1, 0), (1, 0, 0), 0.0), np.eye(4), atol=1e-6)


# -- outcome classification and banners ---------------------------------------


def make_result(simulated=True, success=False, reasons=(), approach_km=5_000.0):
    return types.SimpleNamespace(
        simulated=simulated,
        success=success,
        surface_impact=False,
        reasons=tuple(reasons),
        closest_approach=None if approach_km is None else approach_km * _km(),
        lunar_sphere_of_influence=66_000.0 * _km(),
        available_delta_v=6_200.0 * _ms(),
        tli_delta_v=0.0 * _ms(),
        required_earth_departure_delta_v=9_400.0 * _ms(),
    )


def _ms():
    from astropy import units as u

    return u.m / u.s


def _km():
    from astropy import units as u

    return u.km


def test_classification_matches_the_simulation_verdict():
    from ui.mission_outcome import flight_outcome

    assert flight_outcome(make_result(simulated=False)) == f.FALL
    assert flight_outcome(make_result(simulated=True, success=False)) == f.MISS
    assert flight_outcome(make_result(simulated=True, success=True)) == f.LAND


def test_liftoff_check_matches_the_mission_prescreen():
    from ui.mission_outcome import can_lift_off

    ok = types.SimpleNamespace(thrust=1e6, twr=1.4)
    weak = types.SimpleNamespace(thrust=1e5, twr=1.0)  # the sim requires TWR > 1.0
    none = types.SimpleNamespace(thrust=0.0, twr=0.0)

    assert can_lift_off(ok) == (True, True)
    assert can_lift_off(weak) == (False, True)
    assert can_lift_off(none) == (False, False)


def test_banners_state_the_cause_of_each_failure():
    from ui import mission_outcome as o

    text, color = o.no_liftoff_banner(types.SimpleNamespace(thrust=1e5, twr=0.62))
    assert "cannot lift off" in text and "0.62" in text and color == o.RED
    assert "no engine thrust" in o.no_liftoff_banner(types.SimpleNamespace(thrust=0.0, twr=0.0))[0]

    text, color = o.verdict_banner(
        make_result(simulated=False, reasons=("Insufficient vehicle delta-v.",)), f.FALL
    )
    assert "cannot reach the Moon" in text and "Insufficient vehicle delta-v." in text
    assert color == o.RED

    text, color = o.verdict_banner(make_result(approach_km=12_345.0), f.MISS)
    assert "misses the Moon" in text and "12,345 km" in text and color == o.RED

    text, color = o.verdict_banner(make_result(success=True), f.LAND)
    assert text.startswith("REACHED THE MOON") and color == o.GREEN
    assert "illustration" in text and "not simulated" in text  # no false landing claim

    text, color = o.error_banner(RuntimeError("no network"))
    assert "no verdict" in text and "no network" in text and color == o.AMBER


# -- designer mission events --------------------------------------------------


@pytest.fixture
def designer(monkeypatch, tmp_path):
    ui = SpacecraftDesignerUI(EventBus(), preset_path=tmp_path / "d.json")
    ui.load_lunar_demo()
    monkeypatch.setattr(
        designer_module.dpg,
        "get_value",
        lambda tag: {"lunar_departure_date": "2030-01-01", "lunar_transfer_days": 5.0}[tag],
    )
    monkeypatch.setattr(ui, "_display_mission_result", lambda result: None)
    seen = []
    for name in ("mission.started", "mission.completed", "mission.failed", "mission.cancelled"):
        ui.events.subscribe(name, lambda *args, name=name: seen.append((name, args)))
    return ui, seen


def names(seen):
    return [name for name, _ in seen]


def wait_for_run(ui, timeout=5.0):
    deadline = time.time() + timeout
    while ui._mission_run is not None and ui._mission_run.outcome is None:
        assert time.time() < deadline, "mission run never finished"
        time.sleep(0.005)


def test_run_publishes_started_with_liftoff_check_then_completed(designer, monkeypatch):
    ui, seen = designer
    monkeypatch.setattr(
        designer_module, "run_lunar_flyby_simulation", lambda *a, **k: make_result(success=True)
    )

    ui.run_lunar_mission()

    assert names(seen) == ["mission.started", "mission.completed"]
    assert seen[0][1] == (True, True)  # the starter design can lift off


def test_started_reports_a_vehicle_that_cannot_lift_off(designer, monkeypatch):
    ui, seen = designer
    engine = next(c for c in ui.spacecraft.components if hasattr(c, "thrust"))
    engine.thrust = 1_000.0  # far too weak to lift the vehicle
    ui.refresh()
    monkeypatch.setattr(
        designer_module, "run_lunar_flyby_simulation", lambda *a, **k: make_result(simulated=False)
    )

    ui.run_lunar_mission()

    assert seen[0] == ("mission.started", (False, True))


def test_simulation_error_publishes_failed(designer, monkeypatch):
    ui, seen = designer

    def boom(*args, **kwargs):
        raise RuntimeError("no network")

    monkeypatch.setattr(designer_module, "run_lunar_flyby_simulation", boom)
    ui.run_lunar_mission()

    assert names(seen) == ["mission.started", "mission.failed"]
    assert ui.mission_result is None


def test_background_run_keeps_ui_free_until_polled(designer, monkeypatch):
    ui, seen = designer
    ui.background_missions = True
    release = threading.Event()

    def slow(*args, **kwargs):
        release.wait(5.0)
        return make_result(success=False)

    monkeypatch.setattr(designer_module, "run_lunar_flyby_simulation", slow)
    ui.run_lunar_mission()
    ui.poll_mission()
    ui.run_lunar_mission()  # ignored: already running

    assert names(seen) == ["mission.started"]
    release.set()
    wait_for_run(ui)
    ui.poll_mission()

    assert names(seen) == ["mission.started", "mission.completed"]
    assert ui.mission_result.success is False
    assert not ui.mission_running


def test_editing_the_design_mid_run_discards_the_result(designer, monkeypatch):
    ui, seen = designer
    ui.background_missions = True
    release = threading.Event()

    def slow(*args, **kwargs):
        release.wait(5.0)
        return make_result(success=True)

    monkeypatch.setattr(designer_module, "run_lunar_flyby_simulation", slow)
    ui.run_lunar_mission()
    ui.add_component(None, None, "payload")
    assert names(seen) == ["mission.started", "mission.cancelled"]  # cancelled at once
    release.set()
    ui.poll_mission()
    time.sleep(0.05)
    ui.poll_mission()

    assert names(seen) == ["mission.started", "mission.cancelled"]  # stale result ignored
    assert ui.mission_result is None and not ui.mission_running


def test_poll_does_not_drop_a_run_whose_thread_has_not_started(designer):
    # Regression: DearPyGui button callbacks run on another thread, so the main
    # loop could poll between creating the worker thread and starting it. A run
    # is only finished once its worker has stored an outcome.
    ui, seen = designer
    run = designer_module._MissionRun(ui._mission_serial)
    ui._mission_run = run

    ui.poll_mission()
    assert ui.mission_running and names(seen) == []  # still running, not dropped

    run.outcome = (make_result(success=True), None)
    ui.poll_mission()
    assert names(seen) == ["mission.completed"] and not ui.mission_running


def test_run_started_from_another_thread_is_always_applied(designer, monkeypatch):
    ui, seen = designer
    ui.background_missions = True
    monkeypatch.setattr(
        designer_module, "run_lunar_flyby_simulation", lambda *a, **k: make_result(success=True)
    )
    for attempt in range(60):
        seen.clear()
        presser = threading.Thread(target=ui.run_lunar_mission)  # like a dpg callback
        presser.start()
        deadline = time.time() + 5.0
        while "mission.completed" not in names(seen):
            ui.poll_mission()  # the main loop polling every frame, racing the start
            assert time.time() < deadline, f"run {attempt} never completed"
        presser.join()
        assert not ui.mission_running


def test_worker_crash_is_reported_not_swallowed(designer, monkeypatch):
    ui, seen = designer
    ui.background_missions = True

    class Fatal(BaseException):
        pass

    def crash(*args, **kwargs):
        raise Fatal("worker died")

    monkeypatch.setattr(ui, "_compute_mission", crash)
    ui.run_lunar_mission()
    wait_for_run(ui)
    ui.poll_mission()

    assert names(seen) == ["mission.started", "mission.failed"]
    assert not ui.mission_running


def test_run_can_restart_immediately_after_reset_flight(designer, monkeypatch):
    ui, seen = designer
    ui.background_missions = True
    release = threading.Event()
    calls = []

    def sim(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            release.wait(5.0)  # the first run is still busy when the second starts
        return make_result(success=True)

    monkeypatch.setattr(designer_module, "run_lunar_flyby_simulation", sim)
    ui.run_lunar_mission()
    ui.reset_flight()
    ui.run_lunar_mission()  # not blocked by the abandoned run
    wait_for_run(ui)
    ui.poll_mission()
    release.set()

    assert names(seen) == ["mission.started", "mission.cancelled", "mission.started", "mission.completed"]


def test_reset_flight_event_cancels_run(designer):
    ui, _ = designer
    flights = []
    ui.events.subscribe("flight.reset", lambda: flights.append(True))
    serial = ui._mission_serial

    ui.reset_flight()

    assert flights == [True] and ui._mission_serial == serial + 1


# -- callbacks run on the main thread ----------------------------------------


def test_application_runs_widget_callbacks_on_the_main_thread(monkeypatch):
    from ui import application as module

    dpg = module.dpg
    dpg.reset_mock()
    app = module.Application()
    app.initialize()

    kwargs = dpg.configure_app.call_args.kwargs
    assert kwargs["manual_callback_management"] is True

    dpg.get_callback_queue.return_value = [("job-1",), ("job-2",)]
    app.render()

    assert [c.args[0] for c in dpg.run_callbacks.call_args_list] == [[("job-1",)], [("job-2",)]]
    dpg.render_dearpygui_frame.assert_called_once()


def test_a_failing_callback_does_not_stop_the_frame_loop(monkeypatch, capsys):
    from ui import application as module

    dpg = module.dpg
    dpg.reset_mock()
    dpg.get_callback_queue.return_value = [("bad",), ("good",)]
    dpg.run_callbacks.side_effect = [RuntimeError("callback bug"), None]
    try:
        module.Application().render()
    finally:
        dpg.run_callbacks.side_effect = None

    assert dpg.run_callbacks.call_count == 2  # the second job still ran
    dpg.render_dearpygui_frame.assert_called_once()
    assert "callback bug" in capsys.readouterr().err


# -- viewport / application integration (real OpenGL) -------------------------


@pytest.fixture(scope="module")
def renderer():
    return OpenGLRenderer()


def play(viewport, renderer, seconds, states):
    for _ in range(int(seconds * 30)):
        viewport.update(1 / 30)
        renderer.begin_frame()
        viewport.render(renderer)
        states.add(viewport.flight.state)


def test_viewport_renders_every_outcome(renderer):
    craft = load_spacecraft(DEFAULT_PRESET)
    viewport = SpacecraftViewport(lambda: craft)
    states = set()
    for outcome in (f.LAND, f.MISS, f.FALL):
        viewport.start_flight()
        play(viewport, renderer, 5.0, states)
        viewport.finish_flight(outcome)
        play(viewport, renderer, 14.0, states)
        assert viewport.flight.finished
        viewport.reset_flight()
    viewport.start_flight(liftoff=False)
    play(viewport, renderer, 4.0, states)

    assert states >= {
        f.ASCENDING, f.DESCENDING, f.LANDED, f.FLYBY, f.LOST,
        f.FALLING, f.CRASHED, f.NO_LIFTOFF,
    }
    assert viewport.pick(renderer, 0.5, 0.5) is None  # no picking while flying


def test_camera_follows_the_vehicle_up(renderer):
    craft = load_spacecraft(DEFAULT_PRESET)
    viewport = SpacecraftViewport(lambda: craft)
    viewport.update(0.0)
    viewport.render(renderer)
    start_target = viewport.camera.target.copy()
    start_distance = viewport.camera.distance

    viewport.start_flight()
    for _ in range(240):
        viewport.update(1 / 30)

    assert viewport.camera.target[1] > start_target[1] + 5.0
    assert viewport.camera.distance > start_distance


def test_reset_flight_returns_to_pad(renderer):
    craft = load_spacecraft(DEFAULT_PRESET)
    viewport = SpacecraftViewport(lambda: craft)
    viewport.start_flight()
    for _ in range(60):
        viewport.update(1 / 30)

    viewport.reset_flight()
    viewport.render(renderer)

    assert viewport.flight.state == f.IDLE


@pytest.fixture
def app(monkeypatch):
    from ui import designer_application as module

    class FakeAudio:
        def __init__(self):
            self.enabled = True
            self.played = []

        @property
        def status_message(self):
            return "Fake audio ready"

        def play(self, cue):
            if self.enabled:
                self.played.append(cue)
            return None

        def stop(self):
            pass

        def set_enabled(self, enabled):
            self.enabled = enabled

        def close(self):
            pass

    monkeypatch.setattr(module, "OpenGLRenderer", lambda: None)
    monkeypatch.setattr(module, "AudioCues", FakeAudio)
    monkeypatch.setattr(module, "create_dockspace", lambda: None)
    application = module.DesignerApplication()
    application.designer.load_lunar_demo()
    banners = []
    monkeypatch.setattr(application, "_set_banner", lambda text, color: banners.append(text))
    return application, banners


def test_app_plays_takeoff_and_failure_cues(app):
    application, _ = app

    application.events.publish("mission.started", True, True)
    application.events.publish("mission.completed", make_result(success=False))

    assert application.audio.played == ["takeoff", "failure"]


def test_landed_scene_displays_the_selected_flag_on_a_separate_pole():
    from spacecraft.geometry import FLAG_COLORS, FLAG_GRIDS

    craft = Spacecraft(
        "Flag display",
        appearance=SpacecraftAppearance(national_flag="Japan"),
    )
    viewport = SpacecraftViewport(lambda: craft)
    viewport.flight.state = f.LANDED
    viewport.flight.height = 10.0
    viewport.flight.moon_center = np.array((0.0, 0.0, 0.0))
    viewport.flight.moon_radius = 20.0
    viewport.flight.landing_normal = np.array((0.0, 1.0, 0.0))
    viewport.flight.position = np.array((0.0, 25.0, 0.0))

    class RecordingRenderer:
        def __init__(self):
            self.draws = []

        def draw_mesh(self, key, mesh, model, color, **kwargs):
            self.draws.append((key, model, color))

    renderer = RecordingRenderer()
    viewport._render_flight(renderer, viewport.flight.vehicle_matrix())
    flag_colors = {
        color for key, _, color in renderer.draws if key == "box"
    }

    assert set(FLAG_COLORS.values()) & flag_colors == {
        FLAG_COLORS[symbol]
        for row in FLAG_GRIDS["Japan"]
        for symbol in row
    }
    pole = next(draw for draw in renderer.draws if draw[0] == "cylinder")
    assert np.linalg.norm(pole[1][:3, 3] - viewport.flight.position) > 0.0


def test_app_mutes_and_stops_audio_when_disabled(app):
    application, _ = app

    application.events.publish("audio.enabled", False)
    application.events.publish("mission.started", True, True)

    assert not application.audio.enabled
    assert application.audio.played == []


def test_app_lands_on_success_and_says_it_is_an_illustration(app):
    application, banners = app
    application.events.publish("mission.started", True, True)
    run_viewport(application, 6.0)
    application.events.publish("mission.completed", make_result(success=True))
    run_viewport(application, f.LAND_TIME + 1.0)

    assert application.viewport.flight.state == f.LANDED
    assert banners[-1].startswith("REACHED THE MOON") and "illustration" in banners[-1]
    assert application.audio.played[-1] == "success"


def test_app_shows_a_fail_state_for_each_failure(app):
    application, banners = app
    cases = [
        (make_result(simulated=False, reasons=("Insufficient delta-v.",)), f.CRASHED, "cannot reach"),
        (make_result(simulated=True, success=False), f.LOST, "misses the Moon"),
    ]
    for result, final_state, wording in cases:
        application.events.publish("mission.started", True, True)
        run_viewport(application, 6.0)
        application.events.publish("mission.completed", result)
        run_viewport(application, 25.0)
        assert application.viewport.flight.state == final_state
        assert "MISSION FAILED" in banners[-1] and wording in banners[-1]

    application.events.publish("mission.started", False, True)
    run_viewport(application, 4.0)
    application.events.publish("mission.completed", make_result(simulated=False))
    assert application.viewport.flight.state == f.NO_LIFTOFF
    assert "cannot lift off" in banners[-1]
    assert application.audio.played[-1] == "failure"


def test_app_returns_to_pad_after_an_error_or_design_edit(app):
    application, banners = app
    application.events.publish("mission.started", True, True)
    run_viewport(application, 3.0)
    application.events.publish("mission.failed", RuntimeError("offline"))

    assert application.viewport.flight.state == f.IDLE
    assert "SIMULATION ERROR" in banners[-1] and "no verdict" in banners[-1]

    application.events.publish("mission.started", True, True)
    application.designer.add_component(None, None, "payload")
    assert application.viewport.flight.state == f.IDLE
    assert banners[-1].strip() == ""


def run_viewport(application, seconds):
    for _ in range(int(seconds * 30)):
        application.step_flight(1 / 30)


def test_progress_banner_counts_seconds_and_warns_on_slow_runs():
    from ui import mission_outcome as o

    text, color = o.running_banner(3.9)
    assert "3 s" in text and "ephemeris" not in text and color == o.BLUE
    assert "ephemeris" in o.running_banner(o.SLOW_RUN_SECONDS + 1)[0]


def test_app_ticks_the_banner_while_the_simulation_is_running(app, monkeypatch):
    application, banners = app
    release = threading.Event()
    designer = application.designer
    designer.background_missions = True
    monkeypatch.setattr(designer, "_display_mission_result", lambda result: None)
    monkeypatch.setattr(
        designer_module.dpg,
        "get_value",
        lambda tag: {"lunar_departure_date": "2030-01-01", "lunar_transfer_days": 5.0}[tag],
    )
    monkeypatch.setattr(
        designer_module,
        "run_lunar_flyby_simulation",
        lambda *a, **k: release.wait(5.0) and make_result(success=True),
    )
    clock = iter(x * 1.0 for x in range(100))
    monkeypatch.setattr("ui.designer_application.time.monotonic", lambda: next(clock))

    designer.run_lunar_mission()
    before = len(banners)
    for _ in range(3):
        application._update_progress_banner()
    release.set()
    wait_for_run(designer)
    run_viewport(application, 12.0)  # applies the verdict, then the held banner

    assert any(" s" in text for text in banners[before:])  # elapsed seconds shown
    assert banners[-1].startswith("REACHED THE MOON")
