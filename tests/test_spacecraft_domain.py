import math

import pytest

from spacecraft.analysis import (
    MISSION_PROFILES,
    analyze_spacecraft,
    assess_mission,
)
from spacecraft.components import (
    Avionics,
    Battery,
    Engine,
    FuelTank,
    LandingLeg,
    Payload,
    PowerSystem,
    RcsThruster,
    SolarPanel,
    component_from_dict,
    component_from_catalog,
    component_to_dict,
)
from spacecraft.vehicle import Spacecraft


def test_component_validation_rejects_invalid_mass_and_fuel_load():
    with pytest.raises(ValueError, match="dry_mass"):
        Payload(name="Invalid payload", dry_mass=-1.0)

    with pytest.raises(ValueError, match="fuel_mass"):
        FuelTank(
            name="Overfilled tank",
            dry_mass=10.0,
            capacity=100.0,
            fuel_mass=101.0,
            fuel_type="LOX/RP-1",
        )


def test_assembly_analysis_calculates_mass_delta_v_twr_and_burn_time():
    craft = Spacecraft("Test vehicle")
    craft.add_component(
        Engine(
            name="Test engine",
            dry_mass=100.0,
            thrust=9_806.65,
            isp=300.0,
            fuel_type="test propellant",
        )
    )
    craft.add_component(
        FuelTank(
            name="Test tank",
            dry_mass=100.0,
            capacity=500.0,
            fuel_mass=300.0,
            fuel_type="test propellant",
        )
    )
    craft.add_component(Payload(name="Payload", dry_mass=100.0))
    craft.add_component(
        PowerSystem(
            name="Solar array",
            dry_mass=10.0,
            generation_kw=2.0,
            storage_kwh=4.0,
        )
    )

    result = analyze_spacecraft(craft)

    assert result.dry_mass == pytest.approx(310.0)
    assert result.fuel_mass == pytest.approx(300.0)
    assert result.wet_mass == pytest.approx(610.0)
    assert result.thrust == pytest.approx(9_806.65)
    assert result.twr == pytest.approx(9_806.65 / (610.0 * 9.80665))
    assert result.delta_v == pytest.approx(
        300.0 * 9.80665 * math.log(610.0 / 310.0)
    )
    assert result.burn_time == pytest.approx(300.0 / (9_806.65 / (300.0 * 9.80665)))
    assert result.power_generation_kw == pytest.approx(2.0)
    assert result.power_surplus_kw == pytest.approx(2.0)
    assert result.warnings == []


def test_engine_without_compatible_fuel_reports_warning_and_zero_delta_v():
    craft = Spacecraft("Mismatched vehicle")
    craft.add_component(
        Engine(
            name="LOX/RP-1 engine",
            dry_mass=100.0,
            thrust=1_000.0,
            isp=300.0,
            fuel_type="LOX/RP-1",
        )
    )
    craft.add_component(
        FuelTank(
            name="Hydrogen tank",
            dry_mass=20.0,
            capacity=100.0,
            fuel_mass=100.0,
            fuel_type="LOX/LH2",
        )
    )

    result = analyze_spacecraft(craft)

    assert result.delta_v == 0.0
    assert any("does not match" in warning for warning in result.warnings)


def test_mission_assessment_checks_delta_v_and_liftoff_twr():
    profile = MISSION_PROFILES["leo"]
    capable = assess_mission(
        analyze_spacecraft(_vehicle_with_performance(10_000.0, 2.0)),
        profile,
    )
    insufficient_twr = assess_mission(
        analyze_spacecraft(_vehicle_with_performance(10_000.0, 0.8)),
        profile,
    )
    insufficient_delta_v = assess_mission(
        analyze_spacecraft(_vehicle_with_performance(8_000.0, 2.0)),
        profile,
    )

    assert capable.achievable is True
    assert insufficient_twr.achievable is False
    assert any("TWR" in reason for reason in insufficient_twr.reasons)
    assert insufficient_delta_v.achievable is False
    assert insufficient_delta_v.delta_v_margin == pytest.approx(-1_400.0)


def _vehicle_with_performance(delta_v, twr):
    craft = Spacecraft("Performance test")
    dry_mass = 100.0
    wet_mass = dry_mass * math.exp(delta_v / (300.0 * 9.80665))
    fuel_mass = wet_mass - dry_mass
    craft.add_component(
        Engine(
            name="Test engine",
            dry_mass=10.0,
            thrust=twr * wet_mass * 9.80665,
            isp=300.0,
            fuel_type="test propellant",
        )
    )
    craft.add_component(
        FuelTank(
            name="Test tank",
            dry_mass=dry_mass - 10.0,
            capacity=fuel_mass,
            fuel_mass=fuel_mass,
            fuel_type="test propellant",
        )
    )
    return craft


def test_component_catalog_creates_independent_configurable_parts():
    first = component_from_catalog("fuel_tank")
    second = component_from_catalog("fuel_tank")

    assert isinstance(first, FuelTank)
    assert first.id != second.id
    assert first.fuel_mass <= first.capacity


@pytest.mark.parametrize(
    ("catalog_id", "component_type"),
    [
        ("landing_leg", LandingLeg),
        ("rcs_thruster", RcsThruster),
        ("solar_panel", SolarPanel),
        ("battery", Battery),
        ("avionics", Avionics),
    ],
)
def test_new_catalog_components_round_trip_through_serialization(
    catalog_id, component_type
):
    component = component_from_catalog(catalog_id)

    restored = component_from_dict(component_to_dict(component))

    assert isinstance(component, component_type)
    assert restored == component


def test_new_component_validation_rejects_invalid_hardware_values():
    with pytest.raises(ValueError, match="leg_count"):
        LandingLeg(name="Invalid gear", dry_mass=10.0, leg_count=2)
    with pytest.raises(ValueError, match="thrust_n"):
        RcsThruster(
            name="Invalid RCS",
            dry_mass=1.0,
            thrust_n=0.0,
            isp_s=200.0,
            propellant_type="test",
        )
    with pytest.raises(ValueError, match="area_m2"):
        SolarPanel(name="Invalid array", dry_mass=1.0, area_m2=0.0, generation_kw=1.0)
    with pytest.raises(ValueError, match="max_discharge_kw"):
        Battery(
            name="Invalid battery",
            dry_mass=1.0,
            capacity_kwh=1.0,
            max_discharge_kw=-1.0,
        )
    with pytest.raises(ValueError, match="redundancy"):
        Avionics(name="Invalid avionics", dry_mass=1.0, power_draw_kw=0.1, redundancy=0)


def test_subsystem_metrics_aggregate_ratings_without_counting_rcs_as_main_thrust():
    craft = Spacecraft("Subsystem metrics")
    engine = Engine(
        name="Engine",
        dry_mass=10.0,
        thrust=2_000.0,
        isp=300.0,
        fuel_type="test",
        power_draw_kw=0.1,
    )
    craft.add_component(engine)
    craft.add_component(
        FuelTank(
            name="Tank",
            dry_mass=10.0,
            capacity=100.0,
            fuel_mass=50.0,
            fuel_type="test",
        )
    )
    craft.add_component(
        RcsThruster(
            name="RCS",
            dry_mass=1.0,
            thrust_n=40.0,
            isp_s=200.0,
            propellant_type="test",
            thruster_count=4,
            power_draw_kw=0.2,
        )
    )
    craft.add_component(
        SolarPanel(name="Array", dry_mass=1.0, area_m2=4.0, generation_kw=0.4)
    )
    craft.add_component(
        Battery(
            name="Battery",
            dry_mass=1.0,
            capacity_kwh=6.0,
            max_charge_kw=1.0,
            max_discharge_kw=2.0,
        )
    )
    craft.add_component(
        Avionics(name="Avionics", dry_mass=1.0, power_draw_kw=0.3)
    )

    result = analyze_spacecraft(craft)

    assert result.thrust == engine.thrust
    assert result.rcs_thrust_n == pytest.approx(160.0)
    assert result.power_generation_kw == pytest.approx(0.4)
    assert result.power_storage_kwh == pytest.approx(6.0)
    assert result.power_max_charge_kw == pytest.approx(1.0)
    assert result.power_max_discharge_kw == pytest.approx(2.0)
    assert result.power_draw_kw == pytest.approx(0.6)
    assert result.power_surplus_kw == pytest.approx(-0.2)
    assert "Installed electrical load exceeds generation." in result.warnings
