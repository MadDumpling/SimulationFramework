import json
import math

import pytest

from spacecraft import (
    AttitudeLimits,
    DataProvenance,
    Engine,
    FuelTank,
    Gimbal,
    IgnitionLimits,
    LandingGear,
    MissingDataError,
    Payload,
    Spacecraft,
    ThrottleSpec,
    analyze_spacecraft,
    assess_definition,
    mass_properties,
    static_tip_over_angle_deg,
)
from spacecraft.components import (
    component_from_catalog,
    component_from_dict,
    component_to_dict,
)
from spacecraft.presets import load_spacecraft, save_spacecraft

G0 = 9.80665


def make_engine(**overrides):
    values = dict(
        name="Test engine",
        dry_mass=100.0,
        thrust=10_000.0,
        isp=300.0,
        fuel_type="test",
    )
    values.update(overrides)
    return Engine(**values)


# -- provenance ---------------------------------------------------------------


def test_new_parts_default_to_illustrative_and_catalog_says_so():
    assert make_engine().provenance.quality == "illustrative"
    assert "not real" in component_from_catalog("engine").provenance.notes


def test_traceable_provenance_requires_a_source():
    with pytest.raises(ValueError, match="source"):
        DataProvenance(quality="published")
    with pytest.raises(ValueError, match="quality"):
        DataProvenance(quality="rumoured")
    with pytest.raises(ValueError, match="uncertainty"):
        DataProvenance(quality="estimated", uncertainty_pct=-1.0)

    assert DataProvenance(quality="published", source="Doc 1, rev B").is_traceable


# -- engine operating model ---------------------------------------------------


def test_rated_point_matches_declared_thrust_and_isp():
    engine = make_engine()

    assert engine.thrust_at() == pytest.approx(10_000.0)
    assert engine.mass_flow_at() == pytest.approx(10_000.0 / (300.0 * G0))
    assert engine.isp_at() == pytest.approx(300.0)


def test_ambient_pressure_reduces_thrust_but_not_mass_flow():
    engine = make_engine(exit_area_m2=0.02)

    assert engine.thrust_at(ambient_pressure_pa=101_325.0) == pytest.approx(
        10_000.0 - 101_325.0 * 0.02
    )
    assert engine.mass_flow_at() == pytest.approx(10_000.0 / (300.0 * G0))
    assert engine.isp_at(ambient_pressure_pa=101_325.0) < 300.0


def test_exit_area_is_derived_from_sea_level_thrust():
    engine = make_engine(sea_level_thrust=9_000.0)

    assert engine.effective_exit_area() == pytest.approx(1_000.0 / 101_325.0)
    assert engine.thrust_at(ambient_pressure_pa=101_325.0) == pytest.approx(9_000.0)


def test_ambient_correction_without_area_is_an_explicit_error():
    engine = make_engine()

    assert engine.thrust_at(ambient_pressure_pa=0.0) == pytest.approx(10_000.0)
    with pytest.raises(MissingDataError, match="exit_area"):
        engine.thrust_at(ambient_pressure_pa=1_000.0)


def test_throttle_scales_flow_and_chamber_pressure():
    engine = make_engine(
        chamber_pressure_pa=7e6,
        throttle=ThrottleSpec(min_fraction=0.5, max_fraction=1.0),
    )

    assert engine.mass_flow_at(0.5) == pytest.approx(0.5 * engine.rated_mass_flow)
    assert engine.thrust_at(0.5) == pytest.approx(5_000.0)
    assert engine.chamber_pressure_at(0.5) == pytest.approx(3.5e6)
    assert engine.thrust_at(0.0) == 0.0
    assert engine.mass_flow_at(0.0) == 0.0


def test_throttle_outside_range_or_unknown_range_is_rejected():
    throttleable = make_engine(throttle=ThrottleSpec(min_fraction=0.4, max_fraction=1.0))

    with pytest.raises(ValueError, match="outside the engine range"):
        throttleable.thrust_at(0.2)
    with pytest.raises(ValueError, match="outside the engine range"):
        throttleable.thrust_at(1.2)
    with pytest.raises(MissingDataError, match="throttle range"):
        make_engine().thrust_at(0.7)
    with pytest.raises(MissingDataError, match="chamber_pressure"):
        make_engine().chamber_pressure_at()


def test_tabulated_throttle_curve_is_interpolated():
    engine = make_engine(
        throttle=ThrottleSpec(
            min_fraction=0.5,
            max_fraction=1.0,
            curve=((0.5, 0.45, 0.9), (1.0, 1.0, 1.0)),
        )
    )
    flow_fraction, isp_fraction = engine.throttle.response(0.75)

    assert flow_fraction == pytest.approx(0.725)
    assert isp_fraction == pytest.approx(0.95)
    assert engine.thrust_at(1.0) == pytest.approx(10_000.0)
    assert engine.thrust_at(0.5) == pytest.approx(10_000.0 * 0.45 * 0.9)


def test_invalid_propulsion_limits_are_rejected():
    with pytest.raises(ValueError):
        ThrottleSpec(min_fraction=1.5)
    with pytest.raises(ValueError):
        ThrottleSpec(max_fraction=0.9)
    with pytest.raises(ValueError):
        ThrottleSpec(curve=((1.0, 1.0, 1.0), (0.5, 0.5, 1.0)))
    with pytest.raises(ValueError):
        IgnitionLimits(max_ignitions=0)
    with pytest.raises(ValueError):
        IgnitionLimits(min_burn_time_s=5.0, max_burn_time_s=1.0)
    with pytest.raises(ValueError):
        Gimbal(half_angle_deg=95.0)
    with pytest.raises(ValueError, match="sea_level_thrust"):
        make_engine(sea_level_thrust=20_000.0)


def test_restart_and_throttle_flags_distinguish_unknown_from_no():
    assert IgnitionLimits().restartable is None
    assert IgnitionLimits(max_ignitions=1).restartable is False
    assert IgnitionLimits(max_ignitions=3).restartable is True
    assert ThrottleSpec().is_throttleable is None
    assert ThrottleSpec(min_fraction=1.0, max_fraction=1.0).is_throttleable is False


# -- tanks, stages, analysis --------------------------------------------------


def test_residual_propellant_is_carried_but_not_burned():
    craft = Spacecraft("Residual test")
    craft.add_component(make_engine(dry_mass=50.0, thrust=9_806.65))
    craft.add_component(
        FuelTank(
            name="Tank",
            dry_mass=50.0,
            capacity=500.0,
            fuel_mass=400.0,
            residual_propellant=100.0,
            fuel_type="test",
        )
    )

    result = analyze_spacecraft(craft)

    assert result.wet_mass == pytest.approx(500.0)
    assert result.fuel_mass == pytest.approx(300.0)
    assert result.delta_v == pytest.approx(300.0 * G0 * math.log(500.0 / 200.0))


def test_unknown_residual_counts_as_zero_in_analysis():
    tank = component_from_catalog("fuel_tank")

    assert tank.residual_propellant is None
    assert tank.usable_propellant == tank.fuel_mass


def test_stage_must_be_a_positive_integer():
    with pytest.raises(ValueError, match="stage"):
        make_engine(stage=0)
    with pytest.raises(ValueError, match="stage"):
        make_engine(stage=1.5)


# -- mass properties ----------------------------------------------------------


def test_mass_properties_unknown_until_every_part_has_data():
    craft = Spacecraft("MP")
    craft.add_component(make_engine(com_m=(0.0, 1.0, 0.0)))
    craft.add_component(Payload(name="Payload", dry_mass=100.0))

    props = mass_properties(craft)

    assert props.mass == pytest.approx(200.0)
    assert props.com_m is None
    assert props.missing_com == ["Payload"]


def test_mass_properties_com_and_parallel_axis_inertia():
    craft = Spacecraft("MP")
    craft.add_component(
        Payload(name="Low", dry_mass=100.0, com_m=(0.0, 0.0, 0.0), inertia_kgm2=(1.0, 2.0, 3.0))
    )
    craft.add_component(
        Payload(name="High", dry_mass=100.0, com_m=(0.0, 2.0, 0.0), inertia_kgm2=(1.0, 2.0, 3.0))
    )

    props = mass_properties(craft)

    assert props.com_m == pytest.approx((0.0, 1.0, 0.0))
    assert props.inertia_kgm2[0] == pytest.approx(2.0 + 2 * 100.0 * 1.0)  # Ixx: parallel axis in y
    assert props.inertia_kgm2[1] == pytest.approx(4.0)  # Iyy: both on the y axis
    assert props.inertia_kgm2[2] == pytest.approx(6.0 + 2 * 100.0 * 1.0)


def test_mass_properties_include_propellant_as_point_mass():
    craft = Spacecraft("MP")
    craft.add_component(
        FuelTank(
            name="Tank",
            dry_mass=100.0,
            capacity=100.0,
            fuel_mass=100.0,
            fuel_type="test",
            com_m=(0.0, 1.0, 0.0),
            inertia_kgm2=(5.0, 5.0, 5.0),
        )
    )

    wet = mass_properties(craft)
    dry = mass_properties(craft, include_propellant=False)

    assert wet.mass == pytest.approx(200.0)
    assert dry.mass == pytest.approx(100.0)
    assert wet.inertia_kgm2 == pytest.approx((5.0, 5.0, 5.0))  # same COM, point-mass adds none


def test_static_tip_over_angle():
    craft = Spacecraft("Tip")
    craft.add_component(Payload(name="Body", dry_mass=500.0, com_m=(0.0, 3.0, 0.0)))

    assert static_tip_over_angle_deg(craft) is None  # no gear yet

    craft.landing_gear = LandingGear(footprint_radius_m=4.0, foot_plane_y_m=-1.0)
    assert static_tip_over_angle_deg(craft) == pytest.approx(math.degrees(math.atan2(4.0, 4.0)))

    craft.components[0].com_m = (1.0, 3.0, 0.0)
    assert static_tip_over_angle_deg(craft) == pytest.approx(math.degrees(math.atan2(3.0, 4.0)))


# -- persistence --------------------------------------------------------------


def full_vehicle():
    craft = Spacecraft(
        "Full definition",
        revision="rev A",
        provenance=DataProvenance(
            quality="estimated", source="team estimate", uncertainty_pct=10.0, notes="n"
        ),
        landing_gear=LandingGear(
            leg_count=4,
            footprint_radius_m=3.0,
            foot_plane_y_m=-0.5,
            engine_clearance_m=0.4,
            rated_vertical_speed_mps=2.5,
            rated_horizontal_speed_mps=1.0,
        ),
        attitude_limits=AttitudeLimits(max_tilt_deg=12.0, max_rate_dps=5.0),
    )
    craft.add_component(
        make_engine(
            stage=2,
            sea_level_thrust=9_000.0,
            chamber_pressure_pa=6e6,
            throttle=ThrottleSpec(0.4, 1.0, curve=((0.4, 0.38, 0.95), (1.0, 1.0, 1.0))),
            ignition=IgnitionLimits(max_ignitions=3, min_impulse_ns=50.0, tail_off_time_s=0.2),
            gimbal=Gimbal(half_angle_deg=6.0, rate_dps=10.0),
            com_m=(0.0, 0.5, 0.0),
            inertia_kgm2=(10.0, 5.0, 10.0),
            dimensions_m=(2.0, 1.0),
            provenance=DataProvenance(
                quality="published", source="Datasheet X", revision="2024-01", uncertainty_pct=2.0
            ),
        )
    )
    craft.add_component(
        FuelTank(
            name="Tank",
            dry_mass=20.0,
            capacity=100.0,
            fuel_mass=80.0,
            residual_propellant=2.0,
            fuel_type="test",
            stage=2,
        )
    )
    return craft


def test_full_definition_round_trips_through_json(tmp_path):
    craft = full_vehicle()
    craft.layout[craft.components[0].id] = (0.25, 0.75)
    path = tmp_path / "craft.json"

    save_spacecraft(craft, path)
    restored = load_spacecraft(path)

    assert json.loads(path.read_text())["schema_version"] == 2
    assert restored.revision == "rev A"
    assert restored.provenance == craft.provenance
    assert restored.landing_gear == craft.landing_gear
    assert restored.attitude_limits == craft.attitude_limits
    assert restored.layout == craft.layout
    assert restored.components == craft.components
    engine = restored.components[0]
    assert engine.throttle.curve == ((0.4, 0.38, 0.95), (1.0, 1.0, 1.0))
    assert engine.com_m == (0.0, 0.5, 0.0)
    assert engine.thrust_at(0.4) == craft.components[0].thrust_at(0.4)


def test_version_1_presets_load_with_unknowns_and_illustrative_provenance(tmp_path):
    path = tmp_path / "v1.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "name": "Old",
                "components": [
                    {
                        "type": "Engine",
                        "name": "E",
                        "dry_mass": 1.0,
                        "thrust": 100.0,
                        "isp": 300.0,
                        "fuel_type": "x",
                    }
                ],
            }
        )
    )

    craft = load_spacecraft(path)
    engine = craft.components[0]

    assert engine.provenance.quality == "illustrative"
    assert engine.throttle.min_fraction is None
    assert craft.landing_gear is None


def test_component_dict_round_trip_and_bad_nested_data():
    engine = full_vehicle().components[0]

    assert component_from_dict(component_to_dict(engine)) == engine
    bad = component_to_dict(engine)
    bad["throttle"] = {"min_fraction": 2.0}
    with pytest.raises(ValueError, match="ThrottleSpec"):
        component_from_dict(bad)
    bad = component_to_dict(engine)
    bad["provenance"] = {"quality": "published"}
    with pytest.raises(ValueError, match="source"):
        component_from_dict(bad)
    bad = component_to_dict(engine)
    bad["provenance"] = None
    assert component_from_dict(bad).provenance.quality == "illustrative"


# -- readiness ----------------------------------------------------------------


def test_catalog_vehicle_is_prototype_with_blocking_gaps():
    craft = Spacecraft("Catalog")
    for name in ("engine", "fuel_tank", "payload"):
        craft.add_component(component_from_catalog(name))

    report = assess_definition(craft)
    text = report.summary()

    assert report.high_confidence is False
    assert "PROTOTYPE" in report.label
    assert report.illustrative_parts
    for expected in ("landing gear", "throttle range", "ignition", "gimbal", "attitude"):
        assert expected in text
    assert any(g.severity == "blocking" for g in report.gaps)


def test_fully_specified_traceable_vehicle_has_no_blocking_gaps():
    craft = full_vehicle()
    traceable = DataProvenance(
        quality="published", source="Doc", revision="r1", uncertainty_pct=1.0
    )
    craft.provenance = traceable
    for part in craft.components:
        part.provenance = traceable
        part.com_m = (0.0, 1.0, 0.0)
        part.inertia_kgm2 = (1.0, 1.0, 1.0)
    craft.components[0].ignition = IgnitionLimits(
        max_ignitions=2,
        min_impulse_ns=1.0,
        tail_off_time_s=0.1,
        tail_off_impulse_ns=1.0,
        max_burn_time_s=600.0,
    )

    report = assess_definition(craft)

    assert report.blocking == []
    assert report.high_confidence is True
    assert report.label.startswith("TRACEABLE")


def test_stage_association_gaps_are_reported():
    craft = Spacecraft("Stages")
    craft.add_component(make_engine(stage=1))
    craft.add_component(
        FuelTank(name="Upper tank", dry_mass=1.0, capacity=10.0, fuel_mass=10.0, fuel_type="test", stage=2)
    )

    messages = [g.message for g in assess_definition(craft).gaps]

    assert any("stage 1" in m for m in messages)
    assert any("stage 2" in m for m in messages)


def test_estimated_data_without_uncertainty_or_revision_warns():
    craft = Spacecraft("Est", revision="r")
    craft.add_component(
        make_engine(provenance=DataProvenance(quality="estimated", source="me"))
    )

    messages = [g.message for g in assess_definition(craft).gaps]

    assert any("estimated" in m for m in messages)
    assert any("uncertainty" in m for m in messages)
    assert any("revision" in m for m in messages)
