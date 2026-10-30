"""Engine operating-envelope data. ``None`` always means "unknown", never zero."""

from dataclasses import dataclass
import math

from .provenance import MissingDataError

STANDARD_GRAVITY = 9.80665
SEA_LEVEL_PRESSURE = 101_325.0  # Pa


def _optional_nonnegative(name: str, value: float | None) -> None:
    if value is not None and (not math.isfinite(value) or value < 0.0):
        raise ValueError(f"{name} must be a finite nonnegative number")


@dataclass
class ThrottleSpec:
    """Throttle range and (optional) tabulated throttle behaviour.

    Throttle is a fraction of the rated operating point (1.0 = rated). ``curve``
    rows are ``(throttle, mass_flow_fraction, vacuum_isp_fraction)``; with no
    curve the engine is modelled as ideal (mass flow proportional to throttle,
    constant Isp), which is an assumption the readiness report flags.

    ``excluded_ranges`` are open ``(low, high)`` throttle intervals the engine
    must not be operated in (e.g. the Apollo LM descent engine's 65%-92.5%
    non-operating region); their endpoints remain valid operating points.
    """

    min_fraction: float | None = None
    max_fraction: float | None = None
    curve: tuple[tuple[float, float, float], ...] = ()
    excluded_ranges: tuple[tuple[float, float], ...] = ()

    def __post_init__(self) -> None:
        self.curve = tuple(tuple(float(v) for v in row) for row in self.curve)
        self.excluded_ranges = tuple(
            tuple(float(v) for v in row) for row in self.excluded_ranges
        )
        for row in self.excluded_ranges:
            if len(row) != 2 or not all(math.isfinite(v) and v > 0.0 for v in row) or row[0] >= row[1]:
                raise ValueError("excluded throttle ranges must be (low, high) with 0 < low < high")
        for name, value in (("min_fraction", self.min_fraction), ("max_fraction", self.max_fraction)):
            if value is not None and (not math.isfinite(value) or value <= 0.0):
                raise ValueError(f"throttle {name} must be a finite positive number")
        if self.min_fraction is not None and self.min_fraction > 1.0:
            raise ValueError("throttle min_fraction cannot exceed the rated point (1.0)")
        if self.max_fraction is not None and self.max_fraction < 1.0:
            raise ValueError("throttle max_fraction cannot be below the rated point (1.0)")
        for row in self.curve:
            if len(row) != 3 or not all(math.isfinite(v) and v > 0.0 for v in row):
                raise ValueError("throttle curve rows must be 3 positive finite numbers")
        throttles = [row[0] for row in self.curve]
        if throttles != sorted(set(throttles)):
            raise ValueError("throttle curve must have strictly increasing throttle values")

    @property
    def is_throttleable(self) -> bool | None:
        if self.min_fraction is None or self.max_fraction is None:
            return None
        return self.min_fraction < self.max_fraction

    def response(self, throttle: float) -> tuple[float, float]:
        """Return (mass_flow_fraction, vacuum_isp_fraction) at a throttle setting."""
        if not math.isfinite(throttle) or throttle < 0.0:
            raise ValueError("throttle must be a finite nonnegative number")
        if throttle == 0.0:
            return 0.0, 1.0
        if throttle != 1.0:
            if self.min_fraction is None or self.max_fraction is None:
                raise MissingDataError(
                    "throttle range is unknown; only the rated point (1.0) can be evaluated"
                )
            if not self.min_fraction <= throttle <= self.max_fraction:
                raise ValueError(
                    f"throttle {throttle:.3f} is outside the engine range "
                    f"{self.min_fraction:.3f}-{self.max_fraction:.3f}"
                )
        for low, high in self.excluded_ranges:
            if low < throttle < high:
                raise ValueError(
                    f"throttle {throttle:.3f} is in the non-operating region "
                    f"{low:.3f}-{high:.3f}"
                )
        if not self.curve:
            return throttle, 1.0
        if not self.curve[0][0] <= throttle <= self.curve[-1][0]:
            raise ValueError("throttle is outside the tabulated throttle curve")
        for low, high in zip(self.curve, self.curve[1:]):
            if low[0] <= throttle <= high[0]:
                t = (throttle - low[0]) / (high[0] - low[0])
                return (
                    low[1] + t * (high[1] - low[1]),
                    low[2] + t * (high[2] - low[2]),
                )
        return self.curve[0][1], self.curve[0][2]  # single-row curve at its throttle


@dataclass
class IgnitionLimits:
    """Start/restart, burn duration, minimum impulse, and shutdown behaviour."""

    max_ignitions: int | None = None
    min_burn_time_s: float | None = None
    max_burn_time_s: float | None = None
    min_impulse_ns: float | None = None
    tail_off_time_s: float | None = None
    tail_off_impulse_ns: float | None = None

    def __post_init__(self) -> None:
        if self.max_ignitions is not None and self.max_ignitions < 1:
            raise ValueError("max_ignitions must be at least 1")
        for name in (
            "min_burn_time_s",
            "max_burn_time_s",
            "min_impulse_ns",
            "tail_off_time_s",
            "tail_off_impulse_ns",
        ):
            _optional_nonnegative(name, getattr(self, name))
        if (
            self.min_burn_time_s is not None
            and self.max_burn_time_s is not None
            and self.min_burn_time_s > self.max_burn_time_s
        ):
            raise ValueError("min_burn_time_s cannot exceed max_burn_time_s")

    @property
    def restartable(self) -> bool | None:
        if self.max_ignitions is None:
            return None
        return self.max_ignitions > 1


@dataclass
class Gimbal:
    """Thrust-vector authority. ``half_angle_deg == 0`` means a fixed nozzle."""

    half_angle_deg: float | None = None
    rate_dps: float | None = None

    def __post_init__(self) -> None:
        _optional_nonnegative("half_angle_deg", self.half_angle_deg)
        _optional_nonnegative("rate_dps", self.rate_dps)
        if self.half_angle_deg is not None and self.half_angle_deg >= 90.0:
            raise ValueError("half_angle_deg must be below 90")
