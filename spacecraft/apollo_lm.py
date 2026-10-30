"""Apollo Lunar Module descent-stage vehicle definition (design-phase 1968 weights).

Built from LUNAR_DATA.md (sources S1-S5, S12). Only values that package supports
are entered; anything it marks ``unknown`` stays ``None`` so the readiness report
keeps blocking on it. Values the package tags ``published-secondary`` or
``derived`` are recorded as ``estimated`` until checked against a primary source.

Mass basis: the LM separation weight of 33,055 lb (14,993 kg, S4) less the
7,295 kg nominal descent propellant load (S4 Table II). The split of the
remaining 7,698 kg between descent-stage structure, ascent stage, RCS and gear
was not retrieved, so everything except the engine is one derived remainder.
The suspect Apollo 11 touchdown mass (4,932 kg, LUNAR_DATA.md section 6 #1) is
deliberately not used. Centre of mass and inertia are left unknown: the only
published values are for specific touchdown mass states in a different frame.

Frame convention used here: +Y is the vehicle long axis and y=0 is the
footpad-bottom plane (the package's CG height is measured from there).
"""

from pathlib import Path

from .components import Engine, FuelTank, Payload
from .propulsion import Gimbal, IgnitionLimits, ThrottleSpec
from .provenance import DataProvenance
from .vehicle import LandingGear, Spacecraft

LBF = 4.44822
LB = 0.453592
IN = 0.0254

PRESET_PATH = (
    Path(__file__).resolve().parents[1] / "presets" / "spacecraft" / "apollo_lm.json"
)

REVISION = "LM descent, design weights Dec 1967 (S4); engine as of Apollo 11 era"

SEPARATION_MASS_KG = 14_993.0  # 33,055 lb, S4
DESCENT_PROPELLANT_KG = 7_295.0  # 16,082 lb, S4 Table II
MIXTURE_RATIO = 1.6  # oxidizer : fuel by weight, S5 3-4.1
ENGINE_DRY_MASS_KG = 179.0  # 394 lb, S12 (secondary)

RATED_THRUST_N = 10_500.0 * LBF  # S2 maximum rated thrust, 46.7 kN
VACUUM_ISP_FULL_S = 311.0  # S12 (secondary)
VACUUM_ISP_MIN_THROTTLE_S = 285.0  # S12 (secondary)
MIN_THROTTLE = 0.10  # S2
FIXED_THROTTLE_POINT = 0.925  # S2
THROTTLE_CEILING = 0.65  # S2/S4 (raised from 0.60)
CHAMBER_PRESSURE_FULL_PA = 760e3  # 110 psi, S12 (secondary)
EXIT_DIAMETER_M = 59.0 * IN  # 1.499 m, up to Apollo 14 (S12)
EXIT_AREA_M2 = 3.141592653589793 * (EXIT_DIAMETER_M / 2.0) ** 2  # derived, 1.764 m^2
ENGINE_LENGTH_M = 85.0 * IN  # S12, pre-Apollo 15 engine


def _tank_masses() -> tuple[float, float]:
    """Loaded oxidizer and fuel mass per tank (two of each), from mixture ratio."""
    oxidizer = DESCENT_PROPELLANT_KG * MIXTURE_RATIO / (MIXTURE_RATIO + 1.0)
    fuel = DESCENT_PROPELLANT_KG - oxidizer
    return round(oxidizer / 2.0, 1), round(fuel / 2.0, 1)


def build_apollo_lm() -> Spacecraft:
    engine_provenance = DataProvenance(
        quality="estimated",
        source="NASA TN D-7143 (rated thrust, throttle, gimbal, restarts); "
        "Wikipedia Descent propulsion system (Isp, chamber pressure, mass, geometry)",
        revision="TN D-7143 Mar 1973; Wikipedia accessed 2026-10-30",
        notes="Mixed published and published-secondary values; Isp and chamber "
        "pressure at 10% and 100% only, interpolated linearly in between. "
        "Throttle 1.0 is the 10,500 lbf maximum rating; in flight the engine ran "
        "throttled to 65% or at the 92.5% fixed throttle point, with 65%-92.5% "
        "non-operating. Model chamber pressure at 10% throttle is ~83 kPa vs 76 kPa "
        "published. Duty-cycle life 1,000 s (not per-burn). Sea-level performance is "
        "unknown and likely N/A for this vacuum engine; exit area is derived from "
        "the 59 in exit diameter. Tail-off, minimum impulse and gimbal rate unknown.",
    )
    tank_provenance = DataProvenance(
        quality="estimated",
        source="NASA MSC IN 68-FM-78 Table II (propellant mass); Grumman LMA790-2 "
        "3-4.1 (mixture ratio 1.6)",
        revision="S4 29 Mar 1968",
        notes="Loaded masses derived from total descent propellant and mixture ratio, "
        "split equally between the two tanks of each type. Tank capacity unknown: "
        "set equal to loaded mass (a lower bound). Residual/unusable propellant "
        "unknown. Tank dry mass is included in the remainder component.",
    )
    remainder_provenance = DataProvenance(
        quality="estimated",
        source="NASA MSC IN 68-FM-78 (separation weight 33,055 lb, Table II propellant)",
        revision="S4 29 Mar 1968",
        notes="Derived: separation weight minus descent propellant minus engine mass. "
        "Lumps descent-stage structure and tanks, ascent stage with its propellant, "
        "RCS and landing gear; the split was not retrieved.",
    )

    craft = Spacecraft(
        "Apollo Lunar Module (descent)",
        revision=REVISION,
        provenance=DataProvenance(
            quality="estimated",
            source="Ali et al., AAS-26-167 Table 2 (gear geometry from NASA CAD model); "
            "Rogers, 7th Aerospace Mechanisms Symposium 1972",
            revision="NTRS 20260001760",
            notes="Gear geometry measured from a public CAD model and spot-checked by "
            "the authors. Vehicle origin y=0 is the footpad-bottom plane. Allowable "
            "touchdown tilt and angular rate were not found and remain blocking.",
        ),
        landing_gear=LandingGear(
            leg_count=4,
            footprint_radius_m=4.242,
            foot_plane_y_m=0.0,
            # Engine skirt clearance and rated touchdown speeds: not retrieved
            # (the design velocity envelope polygon is only read at axis marks).
        ),
        attitude_limits=None,
    )

    craft.add_component(
        Engine(
            id="lm-dps-engine",
            name="LM descent engine (LMDE/DPS)",
            description="Throttleable hypergolic descent engine, 10:1 throttle ratio.",
            dry_mass=ENGINE_DRY_MASS_KG,
            thrust=RATED_THRUST_N,
            isp=VACUUM_ISP_FULL_S,
            fuel_type="N2O4/Aerozine-50",
            chamber_pressure_pa=CHAMBER_PRESSURE_FULL_PA,
            exit_area_m2=round(EXIT_AREA_M2, 3),
            throttle=ThrottleSpec(
                min_fraction=MIN_THROTTLE,
                max_fraction=1.0,
                curve=(
                    (
                        MIN_THROTTLE,
                        round(MIN_THROTTLE * VACUUM_ISP_FULL_S / VACUUM_ISP_MIN_THROTTLE_S, 4),
                        round(VACUUM_ISP_MIN_THROTTLE_S / VACUUM_ISP_FULL_S, 4),
                    ),
                    (1.0, 1.0, 1.0),
                ),
                excluded_ranges=((THROTTLE_CEILING, FIXED_THROTTLE_POINT),),
            ),
            ignition=IgnitionLimits(max_ignitions=3),  # designed for 2 restarts (S12)
            gimbal=Gimbal(half_angle_deg=6.0),
            dimensions_m=(round(ENGINE_LENGTH_M, 3), round(EXIT_DIAMETER_M, 3)),
            provenance=engine_provenance,
        )
    )

    oxidizer, fuel = _tank_masses()
    for label, mass in (("oxidizer", oxidizer), ("fuel", fuel)):
        for index in (1, 2):
            craft.add_component(
                FuelTank(
                    id=f"lm-descent-{label}-tank-{index}",
                    name=f"Descent {label} tank {index}",
                    dry_mass=0.0,
                    capacity=mass,
                    fuel_mass=mass,
                    fuel_type="N2O4/Aerozine-50",
                    provenance=tank_provenance,
                )
            )

    craft.add_component(
        Payload(
            id="lm-remainder",
            name="LM structure, ascent stage, RCS, gear (derived)",
            dry_mass=round(SEPARATION_MASS_KG - DESCENT_PROPELLANT_KG - ENGINE_DRY_MASS_KG, 1),
            description="Everything except the descent engine and descent propellant.",
            provenance=remainder_provenance,
        )
    )
    return craft
