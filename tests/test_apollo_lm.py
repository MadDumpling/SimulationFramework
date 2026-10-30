import pytest

from spacecraft import (
    Engine,
    FuelTank,
    ThrottleSpec,
    analyze_spacecraft,
    assess_definition,
    mass_properties,
)
from spacecraft.apollo_lm import PRESET_PATH, build_apollo_lm
from spacecraft.components import component_from_dict, component_to_dict
from spacecraft.presets import load_spacecraft
from spacecraft import reference_data as ref

LBF = 4.44822


@pytest.fixture(scope="module")
def lm():
    return build_apollo_lm()


@pytest.fixture(scope="module")
def engine(lm):
    return next(part for part in lm.components if isinstance(part, Engine))


def test_preset_file_matches_builder(lm):
    loaded = load_spacecraft(PRESET_PATH)

    assert loaded.name == lm.name
    assert loaded.revision == lm.revision
    assert loaded.provenance == lm.provenance
    assert loaded.landing_gear == lm.landing_gear
    assert loaded.attitude_limits is None
    assert loaded.components == lm.components


def test_masses_match_published_separation_weight(lm):
    analysis = analyze_spacecraft(lm)

    assert analysis.wet_mass == pytest.approx(14_993.0)  # 33,055 lb (S4)
    assert analysis.fuel_mass == pytest.approx(7_295.0)  # S4 Table II
    assert analysis.dry_mass == pytest.approx(7_698.0)
    assert analysis.thrust == pytest.approx(10_500 * LBF)
    assert analysis.warnings == []


def test_delta_v_agrees_with_published_descent_budget(lm):
    # S4 Table II lists 6,575 ft/s (2,004 m/s) for the whole descent.
    assert analyze_spacecraft(lm).delta_v == pytest.approx(2_004.0, rel=0.02)


def test_propellant_split_follows_mixture_ratio(lm):
    tanks = [p for p in lm.components if isinstance(p, FuelTank)]
    oxidizer = sum(t.fuel_mass for t in tanks if "oxidizer" in t.name)
    fuel = sum(t.fuel_mass for t in tanks if "fuel" in t.name)

    assert len(tanks) == 4
    assert oxidizer / fuel == pytest.approx(1.6, rel=1e-3)


def test_engine_matches_published_throttle_points(engine):
    assert engine.thrust_at(0.10) == pytest.approx(1_050 * LBF, rel=0.01)
    assert engine.isp_at(0.10) == pytest.approx(285.0, rel=0.01)
    assert engine.isp_at(1.0) == pytest.approx(311.0)
    assert engine.thrust_at(0.925) == pytest.approx(9_712.5 * LBF, rel=0.02)
    assert engine.throttle.is_throttleable is True
    assert engine.ignition.restartable is True
    assert engine.gimbal.half_angle_deg == 6.0


def test_non_operating_throttle_region_is_rejected(engine):
    for bad in (0.7, 0.8, 0.92, 0.05):
        with pytest.raises(ValueError):
            engine.thrust_at(bad)
    for good in (0.10, 0.65, 0.925, 1.0):
        assert engine.thrust_at(good) > 0.0


def test_engine_produces_no_net_thrust_at_sea_level_pressure(engine):
    # A 47.5:1 vacuum nozzle cannot overcome 1 atm back-pressure over its exit area.
    assert engine.thrust_at(1.0, ambient_pressure_pa=101_325.0) == 0.0


def test_unknowns_are_left_unknown(lm, engine):
    assert lm.attitude_limits is None
    assert lm.landing_gear.engine_clearance_m is None
    assert lm.landing_gear.rated_vertical_speed_mps is None
    assert engine.gimbal.rate_dps is None
    assert engine.ignition.min_impulse_ns is None
    assert engine.ignition.tail_off_time_s is None
    assert engine.ignition.max_burn_time_s is None
    assert engine.sea_level_thrust is None
    assert all(
        p.residual_propellant is None for p in lm.components if isinstance(p, FuelTank)
    )
    props = mass_properties(lm)
    assert props.com_m is None and props.inertia_kgm2 is None


def test_suspect_apollo_11_mass_is_not_used(lm):
    assert all(part.dry_mass != 4_932.0 for part in lm.components)
    assert mass_properties(lm).mass != pytest.approx(4_932.0)
    assert ref.ADAMS_LIKE.mass_kg is None


def test_readiness_blocks_only_on_the_documented_gaps(lm):
    report = assess_definition(lm)
    blocking = " | ".join(gap.message for gap in report.blocking)

    assert len(report.blocking) == 2
    assert "engine ground clearance" in blocking
    assert "attitude" in blocking
    assert report.high_confidence is False
    assert report.illustrative_parts == []  # nothing is passed off as placeholder
    assert "PROTOTYPE" in report.label


def test_no_part_claims_published_without_checking_secondary_sources(lm):
    qualities = {lm.provenance.quality} | {p.provenance.quality for p in lm.components}

    assert qualities == {"estimated"}


# -- throttle exclusion ranges ------------------------------------------------


def test_excluded_range_validation_and_round_trip(engine):
    with pytest.raises(ValueError, match="excluded"):
        ThrottleSpec(excluded_ranges=((0.9, 0.5),))
    with pytest.raises(ValueError, match="excluded"):
        ThrottleSpec(excluded_ranges=((0.5,),))

    restored = component_from_dict(component_to_dict(engine))
    assert restored.throttle.excluded_ranges == ((0.65, 0.925),)
    assert restored == engine


# -- reference data -----------------------------------------------------------


def test_descent_profile_sums_to_published_totals():
    assert sum(p.delta_v_mps for p in ref.DESCENT_PROFILE) == pytest.approx(
        ref.DESCENT_PROFILE_TOTALS.delta_v_mps, abs=2.0
    )
    # S4 prints 16,082 lb total against 16,080 lb of phase figures: rounding.
    assert sum(p.propellant_kg for p in ref.DESCENT_PROFILE) == pytest.approx(
        ref.DESCENT_PROFILE_TOTALS.propellant_kg, abs=2.0
    )


def test_lm_propellant_load_matches_descent_profile(lm):
    assert analyze_spacecraft(lm).fuel_mass == ref.DESCENT_PROFILE_TOTALS.propellant_kg


def test_site_uses_lro_solution_and_flags_unknowns():
    site = ref.APOLLO_11_SITE

    assert (site.latitude_deg, site.longitude_deg) == (0.67416, 23.47314)
    assert "Mean Earth" in site.frame
    assert site.landing_ellipse_km is None
    assert site.elevation_m is None
    assert site.provenance.quality == "published"
    assert site.slope_provenance.quality == "estimated"


def test_gravity_and_terrain_reference_radii_differ():
    assert ref.GRGM1200A.reference_radius_km == 1738.0
    assert ref.SLDEM2015.reference_radius_km == 1737.4
    assert ref.GRGM1200A.degree_order == 1200
    assert "DE430" in ref.GRGM1200A.frame


def test_touchdown_limits_are_illustrative_and_tilt_rate_stay_blocking():
    limits = ref.APOLLO_TOUCHDOWN_LIMITS

    assert limits.provenance.quality == "illustrative"
    assert limits.max_tilt_deg is None
    assert limits.max_rate_dps is None
    assert (limits.max_vertical_speed_mps, limits.max_horizontal_speed_mps) == (3.05, 1.22)


def test_reconstruction_horizontal_speeds_match_published_values():
    assert ref.ZUPP_LIKE.horizontal_speed_mps == pytest.approx(0.651, abs=1e-3)
    assert ref.ADAMS_LIKE.horizontal_speed_mps == pytest.approx(0.650, abs=1e-3)
    assert len(ref.RECONSTRUCTIONS) == 2
    assert ref.RECONSTRUCTION_PROVENANCE.quality == "estimated"


def test_gap_register_is_complete_and_unique():
    ids = [gap[0] for gap in ref.DATA_GAPS]

    assert ids == [f"G{n}" for n in range(1, 21)]
