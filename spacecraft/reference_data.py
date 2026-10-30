"""Apollo 11 reference data for lunar arrival, descent and validation (Phases 3-5).

Transcribed from LUNAR_DATA.md; section numbers refer to it. Every group carries a
``DataProvenance``. ``published-secondary`` and ``derived`` values are recorded as
``estimated``. ``None`` means the package marks the value unknown; it is never
filled in. Nothing here is consumed by the simulation yet; it is the typed, tested
input for the arrival, descent and validation work.

Not included on purpose: the suspect 4,932 kg "Apollo 11" touchdown mass and its
inertias (section 6 #1), and the Saturn V / launch data (section 2, mostly unknown).
"""

from dataclasses import dataclass

from .provenance import DataProvenance


def _published(source: str, revision: str = "", notes: str = "") -> DataProvenance:
    return DataProvenance(quality="published", source=source, revision=revision, notes=notes)


def _estimated(source: str, notes: str = "", revision: str = "") -> DataProvenance:
    return DataProvenance(quality="estimated", source=source, revision=revision, notes=notes)


# -- Phase 3: site, gravity, terrain, constants -------------------------------


@dataclass(frozen=True)
class LandingSite:
    name: str
    latitude_deg: float
    longitude_deg: float
    frame: str
    ephemeris: str
    planned_latitude_deg: float
    planned_longitude_deg: float
    planned_miss_km: float
    # None = unknown: landing ellipse, elevation (derive from LOLA), hazard terrain.
    landing_ellipse_km: tuple[float, float] | None
    elevation_m: float | None
    touchdown_slope_deg: tuple[float, float]  # tuned in reconstructions, not measured
    provenance: DataProvenance
    slope_provenance: DataProvenance


APOLLO_11_SITE = LandingSite(
    name="Apollo 11, Tranquility Base",
    latitude_deg=0.67416,
    longitude_deg=23.47314,
    frame="Mean Earth/Polar Axis (not the GRGM1200A principal-axes frame)",
    ephemeris="DE421",
    planned_latitude_deg=0.75,
    planned_longitude_deg=23.62,
    planned_miss_km=6.4,
    landing_ellipse_km=None,
    elevation_m=None,
    touchdown_slope_deg=(4.2, 4.5),
    provenance=_published(
        "NSSDC Apollo Landing Site Coordinates (Wagner et al., Icarus 283, 2017); LROC",
        revision="LRO-image based solution",
        notes="Apollo-era 0.6875N, 23.4333E is superseded (about 1.2 km east-west "
        "from this). Convert to the principal-axes frame before using GRGM1200A.",
    ),
    slope_provenance=_estimated(
        "Ali et al., AAS-26-167 Table 5",
        notes="Slope was tuned by trial and error in the touchdown reconstructions.",
    ),
)


@dataclass(frozen=True)
class GravityModelRef:
    name: str
    degree_order: int
    gm_km3_s2: float
    reference_radius_km: float
    frame: str
    alternatives: tuple[str, ...]
    provenance: DataProvenance


GRGM1200A = GravityModelRef(
    name="GRGM1200A",
    degree_order=1200,
    gm_km3_s2=4902.80011526323,
    reference_radius_km=1738.0,
    frame="Lunar body-fixed principal axes, defined by planetary ephemeris DE430",
    alternatives=("GRGM600PRIM1", "GRGM900C2"),
    provenance=_published(
        "PDS GRAIL GRGM1200A spherical-harmonic label; NASA PGDA product 50",
        notes="Mission design resolution goal ~30 km (degree/order ~180); Bouguer "
        "gravity globally accurate to about degree 600. Use this GM for dynamics, "
        "not the rounded fact-sheet value.",
    ),
)


@dataclass(frozen=True)
class TerrainModelRef:
    name: str
    resolution_m: float
    latitude_coverage_deg: float
    reference_radius_km: float
    vertical_accuracy_m: tuple[float, float]
    companion_products: tuple[str, ...]
    provenance: DataProvenance


SLDEM2015 = TerrainModelRef(
    name="SLDEM2015 (LOLA + SELENE/Kaguya Terrain Camera)",
    resolution_m=59.0,
    latitude_coverage_deg=60.0,
    reference_radius_km=1737.4,
    vertical_accuracy_m=(3.0, 4.0),
    companion_products=("slope map", "azimuth map"),
    provenance=_published(
        "NASA PGDA product 54; PDS ODE LOLA SLDEM; USGS Astrogeology",
        notes="~60 m posts do not resolve meter-scale rocks and craters; LROC NAC "
        "DTMs are needed for hazard constraints (unknown here). Topography radius "
        "1737.4 km differs from the 1738.0 km gravity radius.",
    ),
)


@dataclass(frozen=True)
class LunarConstants:
    mass_kg: float
    equatorial_radius_km: float
    polar_radius_km: float
    mean_radius_km: float
    mean_density_kg_m3: float
    surface_gravity_m_s2: float
    escape_velocity_km_s: float
    sidereal_rotation_period_h: float
    obliquity_deg: float
    provenance: DataProvenance


MOON_CONSTANTS = LunarConstants(
    mass_kg=0.07346e24,
    equatorial_radius_km=1738.1,
    polar_radius_km=1736.0,
    mean_radius_km=1737.4,
    mean_density_kg_m3=3344.0,
    surface_gravity_m_s2=1.62,
    escape_velocity_km_s=2.38,
    sidereal_rotation_period_h=655.720,
    obliquity_deg=6.68,
    provenance=_published(
        "NASA NSSDC Moon Fact Sheet",
        notes="Reference constants, not a substitute for the GRAIL gravity field.",
    ),
)


# -- Phase 4: descent profile and touchdown limits ----------------------------


@dataclass(frozen=True)
class DescentPhase:
    name: str
    delta_v_mps: float
    propellant_kg: float
    end_altitude_m: float | None  # gate altitude where the phase ends, if defined


# NASA MSC IN 68-FM-78 Table II, based on the 33,055 lb separation weight. The
# propellant figures sum to 7,294 kg against the printed 7,295 kg total (rounding).
DESCENT_PROFILE = (
    DescentPhase("Braking", 1_596.0, 6_199.0, 2_743.0),  # ends at "high gate", 9,000 ft
    DescentPhase("Final approach", 263.0, 706.0, 152.0),  # ends at "low gate", ~500 ft
    DescentPhase("Landing", 118.0, 319.0, None),
    DescentPhase("Vertical descent", 27.0, 70.0, 0.0),  # ~0.91 m/s from ~19.8 m
)
DESCENT_PROFILE_TOTALS = DescentPhase("Total", 2_004.0, 7_295.0, None)
DESCENT_PROFILE_PROVENANCE = _published(
    "Alphin, Taylor, Kirkland, MSC Internal Note 68-FM-78 Table II",
    revision="29 Mar 1968",
    notes="Design-phase weights, not flight reconstruction. Phase boundary "
    "altitudes differ between sources (section 6 #5); define each explicitly.",
)


@dataclass(frozen=True)
class TouchdownLimits:
    """Proposed defaults for review, not validated mission requirements.

    ``None`` tilt and angular-rate limits were not found and must stay blocking.
    """

    max_vertical_speed_mps: float | None
    max_horizontal_speed_mps: float | None
    max_surface_slope_deg: float | None
    max_tilt_deg: float | None
    max_rate_dps: float | None
    max_primary_compression_m: float
    max_secondary_compression_m: float
    max_secondary_tension_m: float
    provenance: DataProvenance


APOLLO_TOUCHDOWN_LIMITS = TouchdownLimits(
    max_vertical_speed_mps=3.05,
    max_horizontal_speed_mps=1.22,
    max_surface_slope_deg=12.0,
    max_tilt_deg=None,
    max_rate_dps=None,
    max_primary_compression_m=0.812,
    max_secondary_compression_m=0.305,
    max_secondary_tension_m=0.407,
    provenance=DataProvenance(
        quality="illustrative",
        notes="Speeds are the maximum marks on the design envelope axes (the envelope "
        "polygon itself is unknown); slope is the 12 degree certification 'Doghouse'; "
        "strut stroke limits are from Ali et al. Table 3 (published-secondary). "
        "Allowable tilt and angular rate were not found (gap G1).",
    ),
)


# -- Phase 5: Apollo 11 validation case ---------------------------------------


@dataclass(frozen=True)
class TouchdownReconstruction:
    """One published Apollo 11 touchdown reconstruction (body frame, +X up)."""

    name: str
    mass_kg: float | None  # None: the paper's 4,932 kg looks wrong, do not use
    axial_velocity_mps: float
    lateral_velocity_mps: float
    forward_velocity_mps: float
    pitch_roll_yaw_deg: tuple[float, float, float]  # 321 Euler sequence
    pitch_roll_yaw_rate_dps: tuple[float, float, float]
    ground_slope_deg: float
    slope_approach_azimuth_deg: float
    footpad_friction: float
    bearing_coefficient_kn: float  # N/m^p
    compaction_exponent: float
    damping_coefficient_cn: float  # N s/m
    plowing_coefficient_kp: float  # N/m

    @property
    def horizontal_speed_mps(self) -> float:
        return (self.lateral_velocity_mps**2 + self.forward_velocity_mps**2) ** 0.5


ZUPP_LIKE = TouchdownReconstruction(
    name="Zupp-like",
    mass_kg=7_063.5,
    axial_velocity_mps=0.5730,
    lateral_velocity_mps=-0.6147,
    forward_velocity_mps=-0.2130,
    pitch_roll_yaw_deg=(0.9430, 2.5450, 15.09),
    pitch_roll_yaw_rate_dps=(0.0, -2.8648, -0.6188),
    ground_slope_deg=4.5,
    slope_approach_azimuth_deg=0.0,
    footpad_friction=0.33,
    bearing_coefficient_kn=350_254.0,
    compaction_exponent=1.0,
    damping_coefficient_cn=0.0,
    plowing_coefficient_kp=1_454.0,
)

ADAMS_LIKE = TouchdownReconstruction(
    name="Adams-like",
    mass_kg=None,
    axial_velocity_mps=0.5740,
    lateral_velocity_mps=-0.6481,
    forward_velocity_mps=-0.0447,
    pitch_roll_yaw_deg=(1.4827, 2.2937, 0.0),
    pitch_roll_yaw_rate_dps=(0.0, -2.8648, -0.6188),
    ground_slope_deg=4.2,
    slope_approach_azimuth_deg=-12.0,
    footpad_friction=0.36,
    bearing_coefficient_kn=150_000.0,
    compaction_exponent=1.5,
    damping_coefficient_cn=150_000.0,
    plowing_coefficient_kp=1_454.0,
)

RECONSTRUCTIONS = (ZUPP_LIKE, ADAMS_LIKE)
RECONSTRUCTION_PROVENANCE = _estimated(
    "Ali et al., AAS-26-167 (NTRS 20260001760), Tables 1 and 5",
    notes="Tuned to match Apollo 11 and valid only near its conditions; run both "
    "and keep them separate. Engine tail-off during touchdown is part of the case "
    "(Fig. 2, to be digitized). The Adams-like mass set (4,932 kg) is withheld "
    "pending LUNAR_DATA.md section 6 #1.",
)


@dataclass(frozen=True)
class Apollo11Observations:
    """Outcomes a validated touchdown model should reproduce."""

    footpad_penetration_cm: tuple[float, float]
    skid_distance_max_cm: float
    soil_energy_fraction: float
    secondary_tension_stroke_cm: float
    provenance: DataProvenance


APOLLO_11_OBSERVATIONS = Apollo11Observations(
    footpad_penetration_cm=(2.0, 7.62),
    skid_distance_max_cm=7.62,
    soil_energy_fraction=0.60,
    secondary_tension_stroke_cm=10.0,
    provenance=DataProvenance(
        quality="measured",
        source="Mission photography (Ali et al., AAS-26-167); Rogers 1972",
        notes="Photo estimates carry ~0.635 cm uncertainty per measurement.",
        uncertainty_pct=None,
    ),
)


@dataclass(frozen=True)
class CertificationStatistics:
    """Gear certification probabilities, a benchmark for a Monte Carlo run."""

    p_no_strut_fully_strokes: float
    p_stable_slope_le_12deg: float
    p_stable_anywhere_in_site: float
    provenance: DataProvenance


LM_CERTIFICATION = CertificationStatistics(
    p_no_strut_fully_strokes=0.999,
    p_stable_slope_le_12deg=0.998,
    p_stable_anywhere_in_site=0.967,
    provenance=_published(
        "Rogers, Apollo Lunar Module Landing Gear, 7th Aerospace Mechanisms Symposium",
        revision="Nov 1972",
        notes="From statistical slopes and protuberances (Lunar Orbiter photography); "
        "most severe of seven original Apollo sites. Input dispersions unknown.",
    ),
)


# -- Open items ---------------------------------------------------------------

# (id, gap, blocks); the full register with search leads is LUNAR_DATA.md section 7.
DATA_GAPS = (
    ("G1", "Allowable touchdown tilt and angular rate", "success definition"),
    ("G2", "Stage dry masses, tank capacities, residuals, RCS propellant", "Phase 1"),
    ("G3", "Apollo 11 touchdown mass (4,932 kg looks wrong)", "Phase 5 validation"),
    ("G4", "Thrust, chamber pressure, Isp, mass flow vs throttle", "Phase 1 engine model"),
    ("G5", "Sea-level / ambient-pressure behaviour", "Phase 1"),
    ("G6", "Measured throat and exit areas", "Phase 1"),
    ("G7", "Gimbal rate, throttle response, impulse bit, tail-off curve", "Phase 4"),
    ("G8", "RCS thrust, Isp, impulse bit, deadbands", "Phase 4"),
    ("G9", "CG and inertia at intermediate propellant states", "Phase 4"),
    ("G10", "Numeric design touchdown velocity envelope polygon", "Phase 4"),
    ("G11", "Vehicle height/width, engine skirt clearance, as-built footpad span", "Phase 1"),
    ("G12", "Saturn V stage data, launch azimuth, parking-orbit inclination, TLI burn", "Phase 2"),
    ("G13", "Atmosphere, winds, aerodynamics, gravity losses", "Phase 2"),
    ("G14", "Landing ellipse and target region", "Phase 3 'missed site'"),
    ("G15", "Meter-scale terrain and hazards at Tranquility Base", "Phase 3, 4"),
    ("G16", "Apollo 11 SPICE kernels; DE440 coverage check for July 1969", "Phase 3, 5"),
    ("G17", "Navigation/sensor error models; landing radar performance", "Phase 4"),
    ("G18", "Propellant slosh model", "Phase 4"),
    ("G19", "Dispersion distributions for Monte Carlo", "Phase 5"),
    ("G20", "Apollo 11 flight time histories for validation", "Phase 5"),
)
