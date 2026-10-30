"""Report what a vehicle definition is still missing before it can support a landing claim.

``blocking`` gaps are data a powered-descent/touchdown simulation needs and
cannot responsibly assume. ``warning`` gaps limit fidelity or traceability.
"""

from dataclasses import dataclass, field

from .components import Engine, FuelTank
from .mass_properties import mass_properties
from .vehicle import Spacecraft


@dataclass(frozen=True)
class DataGap:
    severity: str  # "blocking" | "warning"
    subject: str
    message: str


@dataclass
class DefinitionReport:
    gaps: list[DataGap] = field(default_factory=list)
    illustrative_parts: list[str] = field(default_factory=list)
    untraceable_parts: list[str] = field(default_factory=list)

    @property
    def blocking(self) -> list[DataGap]:
        return [gap for gap in self.gaps if gap.severity == "blocking"]

    @property
    def high_confidence(self) -> bool:
        """True only when nothing blocks and every part cites measured/published data."""
        return not self.blocking and not self.untraceable_parts

    @property
    def label(self) -> str:
        if self.high_confidence:
            return "TRACEABLE DATA — no blocking gaps"
        return "PROTOTYPE DATA — not valid for landing claims"

    def summary(self) -> str:
        lines = [
            self.label,
            f"{len(self.blocking)} blocking gap(s), "
            f"{len(self.gaps) - len(self.blocking)} warning(s); "
            f"{len(self.illustrative_parts)} illustrative part(s), "
            f"{len(self.untraceable_parts) - len(self.illustrative_parts)} estimated part(s).",
        ]
        lines.extend(f"[{gap.severity.upper()}] {gap.subject}: {gap.message}" for gap in self.gaps)
        return "\n".join(lines)


def assess_definition(spacecraft: Spacecraft) -> DefinitionReport:
    report = DefinitionReport()

    def gap(severity, subject, message):
        report.gaps.append(DataGap(severity, subject, message))

    def check(subject, severity, missing, message):
        if missing:
            gap(severity, subject, message)

    if not spacecraft.revision.strip():
        gap("warning", spacecraft.name, "vehicle definition has no revision identifier")
    _check_provenance(report, spacecraft.name, spacecraft.provenance, "vehicle-level data")

    gear = spacecraft.landing_gear
    if gear is None:
        gap("blocking", spacecraft.name, "no landing gear / contact envelope defined")
    else:
        for name, label in (
            ("leg_count", "leg count"),
            ("footprint_radius_m", "footpad radius"),
            ("foot_plane_y_m", "footpad plane position"),
            ("engine_clearance_m", "engine ground clearance"),
        ):
            check(spacecraft.name, "blocking", getattr(gear, name) is None, f"landing gear {label} unknown")
        check(
            spacecraft.name,
            "warning",
            gear.rated_vertical_speed_mps is None or gear.rated_horizontal_speed_mps is None,
            "landing gear rated touchdown speeds unknown",
        )
    limits = spacecraft.attitude_limits
    check(
        spacecraft.name,
        "blocking",
        limits is None or limits.max_tilt_deg is None or limits.max_rate_dps is None,
        "allowable attitude (tilt) and angular rate not fully specified",
    )

    mass = mass_properties(spacecraft)
    if mass.missing_com:
        gap("warning", spacecraft.name, "centre of mass unknown (no data for: " + ", ".join(mass.missing_com) + ")")
    elif mass.missing_inertia:
        gap(
            "warning",
            spacecraft.name,
            "inertia unknown (no data for: " + ", ".join(mass.missing_inertia)
            + "); only a point-mass model is possible",
        )

    stages_with_engines = {p.stage for p in spacecraft.components if isinstance(p, Engine)}
    stages_with_tanks = {p.stage for p in spacecraft.components if isinstance(p, FuelTank)}

    for part in spacecraft.components:
        _check_provenance(report, part.name, part.provenance, "component data")
        if part.com_m is None and part.dry_mass > 0.0:
            pass  # aggregated into the vehicle-level centre-of-mass gap above
        if isinstance(part, Engine):
            _check_engine(gap, part)
            if part.stage not in stages_with_tanks:
                gap("warning", part.name, f"no propellant tank assigned to stage {part.stage}")
        elif isinstance(part, FuelTank):
            if part.residual_propellant is None:
                gap("warning", part.name, "residual (unusable) propellant unknown; treated as 0")
            if part.stage not in stages_with_engines:
                gap("warning", part.name, f"no engine assigned to stage {part.stage}")
    return report


def _check_provenance(report, subject, provenance, what):
    if provenance.quality == "illustrative":
        report.illustrative_parts.append(subject)
        report.untraceable_parts.append(subject)
        report.gaps.append(DataGap("warning", subject, f"{what} is illustrative, not real hardware data"))
        return
    if not provenance.is_traceable:
        report.untraceable_parts.append(subject)
        report.gaps.append(DataGap("warning", subject, f"{what} is estimated, not measured or published"))
    if provenance.uncertainty_pct is None:
        report.gaps.append(DataGap("warning", subject, f"{what} has no stated uncertainty"))
    if not provenance.revision.strip():
        report.gaps.append(DataGap("warning", subject, f"{what} has no source revision/date"))


def _check_engine(gap, engine):
    if engine.effective_exit_area() is None:
        gap("blocking", engine.name, "exit area or sea-level thrust unknown; cannot correct for ambient pressure")
    if engine.throttle.min_fraction is None or engine.throttle.max_fraction is None:
        gap("blocking", engine.name, "throttle range unknown")
    elif engine.throttle.is_throttleable and not engine.throttle.curve:
        gap("warning", engine.name, "no throttle curve; mass flow and Isp assumed ideal")
    if engine.ignition.max_ignitions is None:
        gap("blocking", engine.name, "ignition/restart limit unknown")
    if engine.gimbal.half_angle_deg is None:
        gap("blocking", engine.name, "gimbal authority unknown (0 = fixed nozzle)")
    elif engine.gimbal.half_angle_deg > 0.0 and engine.gimbal.rate_dps is None:
        gap("warning", engine.name, "gimbal rate unknown")
    if engine.chamber_pressure_pa is None:
        gap("warning", engine.name, "chamber pressure unknown")
    if engine.ignition.min_impulse_ns is None:
        gap("warning", engine.name, "minimum impulse unknown")
    if engine.ignition.tail_off_time_s is None or engine.ignition.tail_off_impulse_ns is None:
        gap("warning", engine.name, "shutdown tail-off behaviour unknown")
    if engine.ignition.max_burn_time_s is None:
        gap("warning", engine.name, "maximum burn duration unknown")
