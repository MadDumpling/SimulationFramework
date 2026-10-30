"""Regression tests: nothing leaks from one mission run into the next.

Covers rerunning after every kind of ending (fell, missed, landed, could not lift
off, simulation error), cancelling mid-run, and editing the design mid-run.
"""

import threading
import time

import numpy as np
import pytest

import ui.spacecraft_designer as designer_module
from viewport import flight as f
from viewport.flight import FlightAnimation

# Shared helpers and fixtures (fixtures are discovered by name in this module).
from test_flight_animation import (  # noqa: F401
    app,
    designer,
    make_result,
    names,
    run,
    run_viewport,
    wait_for_run,
)


# -- the animation itself -----------------------------------------------------


def finish(animation, outcome):
    """Drive a fresh flight to its end state for ``outcome`` (None = no lift-off)."""
    if outcome is None:
        animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0, liftoff=False)
        run(animation, f.STRAIN_TIME + 1.0)
        return
    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)
    run(animation, 15.0)
    animation.conclude(outcome)
    run(animation, 40.0)


ENDINGS = [
    pytest.param(f.FALL, f.CRASHED, id="fell"),
    pytest.param(f.MISS, f.LOST, id="missed"),
    pytest.param(f.LAND, f.LANDED, id="landed"),
    pytest.param(None, f.NO_LIFTOFF, id="no-liftoff"),
]


@pytest.mark.parametrize("outcome,final_state", ENDINGS)
def test_relaunch_after_any_ending_leaves_no_state_behind(outcome, final_state):
    animation = FlightAnimation()
    finish(animation, outcome)
    assert animation.state == final_state and animation.finished

    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)

    assert animation.state == f.ASCENDING and not animation.finished
    assert animation.time == 0.0 and animation.flash_time == 0.0
    assert animation.tilt == 0.0 and animation.flash_center is None
    assert animation.flash() is None and animation.closest_approach is None
    assert animation._exit is None and animation._bezier is None
    assert animation.vehicle_visible  # a vehicle that was "lost" is back
    assert animation.burning
    np.testing.assert_allclose(animation.position, (0.0, 5.0, 0.0))
    np.testing.assert_allclose(animation.velocity, (0.0, 0.0, 0.0))
    np.testing.assert_allclose(animation.orientation, np.eye(4), atol=1e-7)
    np.testing.assert_allclose(animation.vehicle_matrix(), np.eye(4), atol=1e-6)
    np.testing.assert_allclose(animation.landing_normal, (0.0, 1.0, 0.0))


@pytest.mark.parametrize("outcome,final_state", ENDINGS)
def test_second_flight_after_any_ending_matches_a_first_flight(outcome, final_state):
    used, fresh = FlightAnimation(), FlightAnimation()
    finish(used, outcome)
    for animation in (used, fresh):
        animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)
        run(animation, 15.0)
        animation.conclude(f.LAND)
        run(animation, f.LAND_TIME + 1.0)

    assert used.state == fresh.state == f.LANDED
    np.testing.assert_allclose(used.position, fresh.position, atol=1e-9)
    np.testing.assert_allclose(used.orientation, fresh.orientation, atol=1e-9)


def midflight(outcome, seconds):
    """A flight caught mid-motion (climbing, descending, flying by, or falling)."""
    animation = FlightAnimation()
    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)
    if outcome is None:
        run(animation, seconds)  # still climbing
    else:
        run(animation, 15.0)
        animation.conclude(outcome)
        run(animation, seconds)
    return animation


@pytest.mark.parametrize(
    "outcome,seconds,state",
    [
        pytest.param(None, 1.0, f.ASCENDING, id="mid-climb"),
        pytest.param(f.LAND, 3.0, f.DESCENDING, id="mid-descent"),
        pytest.param(f.MISS, 2.0, f.FLYBY, id="mid-flyby"),
        pytest.param(f.FALL, 1.5, f.FALLING, id="mid-fall"),
    ],
)
def test_relaunch_mid_flight_discards_the_motion_in_progress(outcome, seconds, state):
    animation = midflight(outcome, seconds)
    assert animation.state == state
    assert np.linalg.norm(animation.velocity) > 0.0 or state in (f.DESCENDING, f.FLYBY)

    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)

    np.testing.assert_allclose(animation.position, (0.0, 5.0, 0.0))
    np.testing.assert_allclose(animation.velocity, (0.0, 0.0, 0.0))
    np.testing.assert_allclose(animation.orientation, np.eye(4), atol=1e-7)
    assert animation.state == f.ASCENDING and animation.time == 0.0 and animation.tilt == 0.0


# -- the application: verdicts, banners, results ------------------------------


def synchronous_designer(application, monkeypatch, verdicts):
    """The app's designer with the simulation replaced by a queue of results."""
    designer = application.designer
    designer.background_missions = False  # each verdict arrives immediately
    monkeypatch.setattr(designer, "_display_mission_result", lambda result: None)
    monkeypatch.setattr(
        designer_module.dpg,
        "get_value",
        lambda tag: {"lunar_departure_date": "2030-01-01", "lunar_transfer_days": 5.0}[tag],
    )
    queue = iter(verdicts)
    monkeypatch.setattr(
        designer_module, "run_lunar_flyby_simulation", lambda *a, **k: next(queue)
    )
    return designer


@pytest.mark.parametrize(
    "first,first_state,wording",
    [
        pytest.param(
            lambda: make_result(simulated=False, reasons=("Insufficient delta-v.",)),
            f.CRASHED,
            "cannot reach",
            id="fell",
        ),
        pytest.param(
            lambda: make_result(simulated=True, success=False), f.LOST, "misses the Moon", id="missed"
        ),
        pytest.param(lambda: make_result(success=True), f.LANDED, "REACHED THE MOON", id="landed"),
    ],
)
def test_rerun_after_each_verdict_replaces_the_old_banner_and_result(
    app, monkeypatch, first, first_state, wording  # noqa: F811
):
    application, banners = app
    designer = synchronous_designer(application, monkeypatch, [first(), make_result(success=True)])
    animation = application.viewport.flight

    designer.run_lunar_mission()
    run_viewport(application, 40.0)
    assert animation.state == first_state and wording in banners[-1]

    banners_before = len(banners)
    designer.run_lunar_mission()

    # The previous verdict's wording is replaced the moment the rerun begins.
    assert banners[banners_before].startswith("MISSION IN PROGRESS")
    run_viewport(application, f.LAND_TIME + 15.0)
    assert animation.state == f.LANDED
    assert banners[-1].startswith("REACHED THE MOON")
    assert designer.mission_result.success is True


def test_rerun_clears_the_old_result_and_keeps_the_design(app, monkeypatch):  # noqa: F811
    application, _ = app
    designer = synchronous_designer(
        application,
        monkeypatch,
        [make_result(simulated=False, reasons=("Insufficient delta-v.",)), make_result(success=True)],
    )
    design_before = [(c.id, c.dry_mass) for c in designer.spacecraft.components]
    animation = application.viewport.flight

    designer.run_lunar_mission()
    run_viewport(application, 30.0)
    assert animation.state == f.CRASHED and animation.tilt > 1.0
    assert animation.flash_center is not None and designer.mission_result.simulated is False

    seen = {}
    application.events.subscribe(
        "mission.started", lambda *args: seen.update(result=designer.mission_result)
    )
    designer.run_lunar_mission()

    assert seen["result"] is None  # the old verdict is gone when the rerun starts
    assert animation.tilt == 0.0 and animation.flash_center is None  # no wreck carried over
    run_viewport(application, f.LAND_TIME + 15.0)
    assert animation.state == f.LANDED and designer.mission_result.success is True
    assert [(c.id, c.dry_mass) for c in designer.spacecraft.components] == design_before


def test_rerun_after_a_simulation_error_runs_normally(app, monkeypatch):  # noqa: F811
    application, banners = app
    designer = synchronous_designer(application, monkeypatch, [])
    calls = []

    def flaky(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("offline")
        return make_result(success=True)

    monkeypatch.setattr(designer_module, "run_lunar_flyby_simulation", flaky)

    designer.run_lunar_mission()
    assert "SIMULATION ERROR" in banners[-1]
    assert application.viewport.flight.state == f.IDLE and designer.mission_result is None

    designer.run_lunar_mission()
    run_viewport(application, f.LAND_TIME + 15.0)

    assert application.viewport.flight.state == f.LANDED
    assert banners[-1].startswith("REACHED THE MOON")


def test_rerun_after_no_liftoff_flies_once_the_vehicle_is_fixed(app, monkeypatch):  # noqa: F811
    application, banners = app
    designer = synchronous_designer(
        application, monkeypatch, [make_result(simulated=False), make_result(success=True)]
    )
    engine = next(c for c in designer.spacecraft.components if hasattr(c, "thrust"))
    working_thrust = engine.thrust
    engine.thrust = 1_000.0  # far too weak to lift the vehicle
    designer.refresh()

    designer.run_lunar_mission()
    run_viewport(application, 5.0)
    assert application.viewport.flight.state == f.NO_LIFTOFF
    assert "cannot lift off" in banners[-1]

    engine.thrust = working_thrust  # the user fixes the design and presses Run again
    designer.refresh()
    designer.run_lunar_mission()
    run_viewport(application, f.LAND_TIME + 15.0)

    assert application.viewport.flight.state == f.LANDED


def test_design_edit_after_a_failure_clears_the_banner_and_wreck(app, monkeypatch):  # noqa: F811
    application, banners = app
    designer = synchronous_designer(application, monkeypatch, [make_result(simulated=False)])
    designer.run_lunar_mission()
    run_viewport(application, 30.0)
    assert application.viewport.flight.state == f.CRASHED

    designer.add_component(None, None, "payload")

    assert application.viewport.flight.state == f.IDLE
    assert banners[-1].strip() == ""


# -- a fast verdict must not cut the flight short ------------------------------
# Regression: the vehicle pre-check can answer in milliseconds. The verdict used to
# be applied the instant it arrived, so a failing design tipped over on the pad on
# every rerun ("it fails instantly the next time") instead of flying up first.


def hover_lift(animation):
    return f.HOVER_HEIGHT * animation.height


def fly_until_verdict_applies(animation, outcome, verdict_after):
    """Launch, deliver the verdict ``verdict_after`` seconds in; track the peak climb."""
    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)
    run(animation, verdict_after)
    animation.conclude(outcome)
    climbed = 0.0
    for _ in range(60 * 30):
        animation.update(1 / 60)
        # Include the frame in which the verdict takes effect: it is the last climb step.
        climbed = max(climbed, animation.position[1] - 5.0)
        if animation.state != f.ASCENDING:
            break
    return climbed


@pytest.mark.parametrize("outcome", [f.FALL, f.MISS, f.LAND])
@pytest.mark.parametrize("verdict_after", [0.0, 0.02, 0.5, 1.5])
def test_early_verdict_is_held_until_the_vehicle_reaches_hover(outcome, verdict_after):
    animation = FlightAnimation()

    climbed = fly_until_verdict_applies(animation, outcome, verdict_after)

    assert animation.state != f.ASCENDING  # the verdict did get applied
    assert climbed >= 0.97 * hover_lift(animation) - 1e-6  # ...but only after the climb
    assert not animation.pending


def test_verdict_at_launch_keeps_the_vehicle_climbing_not_falling_on_the_pad():
    animation = FlightAnimation()
    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)
    animation.conclude(f.FALL)  # instant verdict, ship has not moved yet

    assert animation.state == f.ASCENDING and animation.pending and animation.burning
    run(animation, 0.5)
    assert animation.state == f.ASCENDING
    assert animation.position[1] > 5.0 and animation.tilt == 0.0  # climbing, not tipped over


def test_only_the_first_pending_verdict_counts():
    animation = FlightAnimation()
    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)
    animation.conclude(f.FALL)
    animation.conclude(f.LAND)
    run(animation, 15.0)

    assert animation.state in (f.FALLING, f.CRASHED)


def test_relaunch_drops_a_pending_verdict():
    animation = FlightAnimation()
    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)
    animation.conclude(f.FALL)
    assert animation.pending

    animation.launch(center=(0.0, 5.0, 0.0), height=10.0, core_radius=1.0)
    run(animation, 20.0)

    assert not animation.pending and animation.state == f.ASCENDING  # hovers, no stale fall


def test_repeated_failing_reruns_each_climb_before_failing(app, monkeypatch):  # noqa: F811
    application, banners = app
    verdicts = [make_result(simulated=False, reasons=("Insufficient delta-v.",))] * 4
    designer = synchronous_designer(application, monkeypatch, verdicts)
    animation = application.viewport.flight

    for attempt in range(4):
        banners_before = len(banners)
        designer.run_lunar_mission()  # the verdict arrives instantly, as on a real rerun

        # Every run starts from the pad: no position, tilt or wreck carried over.
        np.testing.assert_allclose(animation.position, animation.pivot)
        assert animation.tilt == 0.0 and animation.flash_center is None
        assert animation.state == f.ASCENDING and animation.pending

        peak, crashed_early = 0.0, False
        for _ in range(30 * 40):
            application.step_flight(1 / 30)
            peak = max(peak, float(animation.position[1] - animation.pivot[1]))
            if animation.state == f.ASCENDING:
                # The failure banner must wait until the ship has actually climbed.
                assert banners[-1].startswith("MISSION IN PROGRESS")
            if animation.state in (f.FALLING, f.CRASHED) and peak < 0.97 * hover_lift(animation):
                crashed_early = True
            if animation.state == f.CRASHED and animation.time > 1.0:
                break

        assert not crashed_early, f"attempt {attempt + 1} failed before the ship climbed"
        assert peak >= 0.97 * hover_lift(animation), f"attempt {attempt + 1} did not fly up"
        assert animation.state == f.CRASHED
        assert "cannot reach the Moon" in banners[-1]
        assert banners[banners_before].startswith("MISSION IN PROGRESS")


def test_failure_banner_waits_for_the_verdict_to_appear_on_screen(app, monkeypatch):  # noqa: F811
    application, banners = app
    designer = synchronous_designer(application, monkeypatch, [make_result(success=True)])

    designer.run_lunar_mission()
    application.step_flight(1 / 30)
    assert banners[-1].startswith("MISSION IN PROGRESS")  # verdict known, ship still climbing

    run_viewport(application, f.LAND_TIME + 15.0)
    assert banners[-1].startswith("REACHED THE MOON")


def test_cancelling_while_a_verdict_is_held_drops_the_banner_too(app, monkeypatch):  # noqa: F811
    application, banners = app
    designer = synchronous_designer(application, monkeypatch, [make_result(simulated=False)])

    designer.run_lunar_mission()  # verdict held, banner held
    designer.reset_flight()
    run_viewport(application, 20.0)

    assert application.viewport.flight.state == f.IDLE
    assert banners[-1].strip() == ""  # the held failure banner never appears


# -- cancelling ---------------------------------------------------------------


@pytest.fixture
def slow_simulation(designer, monkeypatch):  # noqa: F811
    """A designer whose first simulation blocks until released, then says success."""
    ui, seen = designer
    ui.background_missions = True
    release = threading.Event()
    statuses = []
    monkeypatch.setattr(
        designer_module.SpacecraftDesignerUI,
        "_set_lunar_status",
        staticmethod(lambda status, details: statuses.append(status)),
    )
    monkeypatch.setattr(
        designer_module,
        "run_lunar_flyby_simulation",
        lambda *a, **k: release.wait(5.0) and make_result(success=True),
    )
    yield ui, seen, statuses, release
    release.set()


def test_reset_flight_mid_run_does_not_leave_the_running_status(slow_simulation):
    ui, seen, statuses, release = slow_simulation

    ui.run_lunar_mission()
    assert statuses[-1].startswith("Mission simulation running")
    ui.reset_flight()
    release.set()

    assert statuses[-1].startswith("Mission cancelled")
    assert ui.mission_result is None and not ui.mission_running


def test_editing_the_design_mid_run_does_not_leave_the_running_status(slow_simulation):
    ui, seen, statuses, release = slow_simulation

    ui.run_lunar_mission()
    ui.add_component(None, None, "payload")
    release.set()

    assert statuses[-1].startswith("Mission cancelled")
    assert ui.mission_result is None and not ui.mission_running
    assert names(seen) == ["mission.started", "mission.cancelled"]


def test_cancelled_run_never_overwrites_the_rerun_result(designer, monkeypatch):  # noqa: F811
    ui, seen = designer
    ui.background_missions = True
    release_old = threading.Event()
    calls = []

    def sim(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            release_old.wait(5.0)
            return make_result(success=True)  # the abandoned run would claim success
        return make_result(success=False)

    monkeypatch.setattr(designer_module, "run_lunar_flyby_simulation", sim)
    ui.run_lunar_mission()
    ui.reset_flight()
    ui.run_lunar_mission()
    wait_for_run(ui)
    release_old.set()
    time.sleep(0.05)  # the abandoned worker finishes after the rerun did
    ui.poll_mission()
    ui.poll_mission()

    assert ui.mission_result.success is False  # the rerun's result, not the stale one
    assert names(seen).count("mission.completed") == 1
