"""Source-backed Apollo 11 launch and translunar-injection reference data.

The values are a post-launch operational trajectory, not a reconstruction from
raw telemetry or a predictive vehicle model.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Apollo11Event:
    """An event time in the report's nominal/predicted sequence."""

    elapsed_seconds: float
    phase: str
    label: str


@dataclass(frozen=True)
class TrajectoryAnchor:
    """A trajectory condition copied from the NASA summary table."""

    elapsed_seconds: float
    altitude_m: float | None = None
    geocentric_radius_m: float | None = None
    inertial_velocity_m_s: float | None = None
    flight_path_angle_deg: float | None = None
    inclination_deg: float | None = None
    descending_node_deg: float | None = None
    eccentricity: float | None = None
    orbital_period_s: float | None = None
    apogee_radius_m: float | None = None
    perigee_radius_m: float | None = None


@dataclass(frozen=True)
class Apollo11ReferenceMission:
    """Fixed Apollo 11 mission data from NASA contractor report CR-61291."""

    mission: str
    launch_date_utc: str
    launch_time_utc: str
    launch_time_basis: str
    launch_site: str
    launch_latitude_deg: float
    launch_longitude_east_deg: float
    launch_azimuth_deg: float
    maximum_dynamic_pressure_time_s: float
    maximum_dynamic_pressure_pa: float
    events: tuple[Apollo11Event, ...]
    s_ic_outboard_cutoff: TrajectoryAnchor
    s_ii_cutoff: TrajectoryAnchor
    s_ivb_first_burn_cutoff: TrajectoryAnchor
    parking_orbit: TrajectoryAnchor
    tli: TrajectoryAnchor
    source_id: str
    source_title: str
    source_url: str
    source_tables: str
    fidelity_note: str


APOLLO_11_REFERENCE = Apollo11ReferenceMission(
    mission="Apollo 11 / Saturn V AS-506",
    launch_date_utc="1969-07-16",
    launch_time_utc="13:32:00.5",
    launch_time_basis=(
        "Derived to 0.1 s from the report's 13:31:43.02 GMT guidance-reference "
        "release and -17.5 s first-motion offset."
    ),
    launch_site="Launch Complex 39A, Kennedy Space Center",
    launch_latitude_deg=28.608422,
    launch_longitude_east_deg=279.395867,
    launch_azimuth_deg=72.063,
    maximum_dynamic_pressure_time_s=81.0,
    maximum_dynamic_pressure_pa=34_725.243,
    events=(
        Apollo11Event(0.0, "Launch", "First motion / liftoff"),
        Apollo11Event(135.0, "S-IC", "Center-engine cutoff"),
        Apollo11Event(160.819, "S-IC", "Outboard-engine cutoff"),
        Apollo11Event(161.6, "Staging", "S-IC/S-II separation complete"),
        Apollo11Event(162.2, "S-II", "Engine start sequence initiated"),
        Apollo11Event(163.2, "S-II", "Engine ignition"),
        Apollo11Event(165.219, "S-II", "90% thrust"),
        Apollo11Event(462.0, "S-II", "Center-engine cutoff"),
        Apollo11Event(551.384, "S-II", "Engine cutoff"),
        Apollo11Event(552.3, "Staging", "S-II/S-IVB separation complete"),
        Apollo11Event(555.4, "S-IVB", "First-burn engine ignition"),
        Apollo11Event(557.884, "S-IVB", "First-burn 90% thrust"),
        Apollo11Event(699.22793, "S-IVB", "First guidance cutoff (GCS1)"),
        Apollo11Event(699.8, "Orbit", "Earth parking-orbit insertion"),
        Apollo11Event(9857.5, "S-IVB", "Second-burn 90% thrust"),
        Apollo11Event(10203.801, "TLI", "Second guidance cutoff (GCS2)"),
    ),
    s_ic_outboard_cutoff=TrajectoryAnchor(
        elapsed_seconds=160.819,
        altitude_m=66_731.0,
        inertial_velocity_m_s=2_755.6109,
        flight_path_angle_deg=70.365148,
    ),
    s_ii_cutoff=TrajectoryAnchor(
        elapsed_seconds=551.384,
        altitude_m=187_986.0,
        inertial_velocity_m_s=6_938.8816,
        flight_path_angle_deg=89.33912,
    ),
    s_ivb_first_burn_cutoff=TrajectoryAnchor(
        elapsed_seconds=699.22793,
        altitude_m=191_339.56,
        inertial_velocity_m_s=7_791.4071,
        flight_path_angle_deg=90.002205,
    ),
    parking_orbit=TrajectoryAnchor(
        elapsed_seconds=699.8,
        geocentric_radius_m=6_563_308.7,
        inertial_velocity_m_s=7_793.1014,
        flight_path_angle_deg=90.001449,
        inclination_deg=32.531447,
        descending_node_deg=123.10042,
        eccentricity=0.0010449,
        orbital_period_s=5_284.3769,
    ),
    tli=TrajectoryAnchor(
        elapsed_seconds=10_203.801,
        geocentric_radius_m=6_714_982.9,
        inertial_velocity_m_s=10_831.069,
        flight_path_angle_deg=82.588522,
        inclination_deg=31.379103,
        descending_node_deg=121.86592,
        eccentricity=0.97667179,
        apogee_radius_m=559_401_776.0,
        perigee_radius_m=6_601_924.0,
        orbital_period_s=1_498_291.321,
    ),
    source_id="NASA-CR-61291",
    source_title=(
        'AS-506 "G" Manned Lunar Landing Mission Post-Launch Operational '
        "Trajectory for July 16, 1969"
    ),
    source_url=(
        "https://ntrs.nasa.gov/api/citations/19690026499/downloads/"
        "19690026499.pdf"
    ),
    source_tables="Tables 2.1 and 2.4",
    fidelity_note=(
        "This is a fixed historical reference profile. Table 2.1 labels its "
        "event sequence predicted; the report is not raw telemetry and does "
        "not define a validated Saturn V propulsion, aerodynamic, or guidance "
        "model for predicting alternate designs."
    ),
)


def format_elapsed_time(elapsed_seconds: float) -> str:
    """Format seconds from first motion as a stable T+HH:MM:SS.ss string."""
    centiseconds = round(elapsed_seconds * 100)
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    seconds, fraction = divmod(remainder, 100)
    return f"T+{hours:02}:{minutes:02}:{seconds:02}.{fraction:02}"
