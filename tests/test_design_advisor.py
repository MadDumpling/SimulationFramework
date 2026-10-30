from astropy import units as u

from spacecraft.advisor import advise_design, format_advice
from spacecraft.analysis import MISSION_PROFILES, analyze_spacecraft
from spacecraft.components import component_from_catalog
from spacecraft.vehicle import Spacecraft
from ui.mission_report_pdf import (
    build_mission_report_text,
    export_mission_report_pdf,
)


def test_advisor_ranks_liftoff_and_propellant_blockers_before_lower_severity():
    craft = Spacecraft("Bottleneck demo")
    engine = component_from_catalog("engine")
    engine.thrust = 1_000.0
    craft.add_component(engine)
    tank = component_from_catalog("fuel_tank")
    tank.fuel_type = "Incompatible propellant"
    craft.add_component(tank)
    craft.add_component(component_from_catalog("avionics"))

    advice = advise_design(
        craft,
        analyze_spacecraft(craft),
        MISSION_PROFILES["moon_transfer"],
    )

    assert [item.severity for item in advice[:3]] == [
        "CRITICAL",
        "CRITICAL",
        "HIGH",
    ]
    assert advice[0].title == "Insufficient liftoff thrust margin"
    assert advice[1].title == "No usable compatible propellant"
    assert "TWR" in advice[0].evidence
    assert "propellant type" in advice[1].suggested_action
    formatted = format_advice(advice)
    assert "1. [CRITICAL] Insufficient liftoff thrust margin" in formatted
    assert "2. [CRITICAL] No usable compatible propellant" in formatted


def test_advisor_ranks_trajectory_miss_and_surface_impact_cautions():
    craft = Spacecraft("Encounter review")
    for part in (
        component_from_catalog("engine"),
        component_from_catalog("fuel_tank"),
        component_from_catalog("solar_panel"),
    ):
        craft.add_component(part)
    analysis = analyze_spacecraft(craft)

    class Quantity:
        def __init__(self, value):
            self.value = value

        def to_value(self, unit):
            return self.value

    class Result:
        simulated = True
        success = False
        surface_impact = False
        closest_approach = Quantity(80_000.0)
        lunar_sphere_of_influence = Quantity(66_000.0)
        required_earth_departure_delta_v = Quantity(9_400.0)
        tli_delta_v = Quantity(3_200.0)
        available_delta_v = Quantity(14_000.0)

    advice = advise_design(
        craft,
        analysis,
        MISSION_PROFILES["moon_transfer"],
        Result(),
    )

    assert next(item for item in advice if "trajectory misses" in item.title.lower()).severity == "HIGH"
    assert "14,000.0 km outside" in next(
        item.evidence for item in advice if "trajectory misses" in item.title.lower()
    )


def test_mission_report_pdf_contains_vehicle_and_advisor(tmp_path):
    craft = Spacecraft("PDF Demo")
    craft.add_component(component_from_catalog("engine"))
    analysis = analyze_spacecraft(craft)
    mission = MISSION_PROFILES["moon_transfer"]
    advice = advise_design(craft, analysis, mission)
    report = build_mission_report_text(craft, analysis, mission, advice)
    destination = tmp_path / "mission.pdf"

    written = export_mission_report_pdf(destination, report)
    data = written.read_bytes()

    assert written == destination
    assert data.startswith(b"%PDF-")
    assert data.rstrip().endswith(b"%%EOF")
    assert written.stat().st_size > 1_000
    assert b"RANKED DESIGN ADVISOR" in data
    assert "RANKED DESIGN ADVISOR" in report
    assert "PDF Demo" in report
    xref_offset = int(data.split(b"startxref\n", 1)[1].splitlines()[0])
    assert data[xref_offset:].startswith(b"xref\n")
    _, object_count = data[xref_offset:].splitlines()[1].split()
    entries = data[xref_offset:].splitlines()[3 : 3 + int(object_count) - 1]
    for object_id, entry in enumerate(entries, start=1):
        offset = int(entry[:10])
        assert data[offset:].startswith(f"{object_id} 0 obj\n".encode("ascii"))


def test_mission_report_pdf_includes_lunar_result_and_ranked_advice():
    craft = Spacecraft("Arrival Report")
    craft.add_component(component_from_catalog("engine"))
    analysis = analyze_spacecraft(craft)
    mission = MISSION_PROFILES["moon_transfer"]
    advice = advise_design(craft, analysis, mission)

    class Quantity:
        def __init__(self, value):
            self.value = value

        def to_value(self, unit):
            return self.value

    class Result:
        simulated = True
        success = True
        surface_impact = False
        available_delta_v = Quantity(14.0)
        required_earth_departure_delta_v = Quantity(9.4)
        tli_delta_v = Quantity(3.2)
        transfer_time = Quantity(5.0)
        closest_approach = Quantity(5_000.0)
        lunar_sphere_of_influence = Quantity(66_000.0)
        closest_approach_time = "2030-01-06"
        relative_speed_at_closest_approach_mps = 800.0
        departure_time = "2030-01-01"
        arrival_time = "2030-01-06"
        trajectory_points = 100
        integrator = "DOP853"
        integration_max_step_s = 300.0
        integration_rtol = 1e-9
        integration_atol = 1e-3
        data_source = "JPL DE440s"
        reasons = ()
        assumptions = ()
        vehicle_warnings = ()

    # Real quantities are used by the mission-report formatter.
    result = Result()
    result.available_delta_v = 14.0 * u.km / u.s
    result.required_earth_departure_delta_v = 9.4 * u.km / u.s
    result.tli_delta_v = 3.2 * u.km / u.s
    result.transfer_time = 5.0 * u.day
    result.closest_approach = 5_000.0 * u.km
    result.lunar_sphere_of_influence = 66_000.0 * u.km

    report = build_mission_report_text(craft, analysis, mission, advice, result)

    assert "LUNAR ARRIVAL" in report
    assert "RANKED DESIGN ADVISOR" in report
    assert "ARRIVAL IS NOT LANDING" in report
