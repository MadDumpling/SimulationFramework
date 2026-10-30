"""Traceability metadata for vehicle data values."""

from dataclasses import dataclass
import math

QUALITIES = ("measured", "published", "estimated", "illustrative")
TRACEABLE_QUALITIES = ("measured", "published")


class MissingDataError(ValueError):
    """A calculation needs a value the vehicle definition leaves unknown."""


@dataclass
class DataProvenance:
    """Where a component's (or vehicle's) numbers came from.

    ``quality`` is one of:
      measured     - from test/flight telemetry or direct measurement
      published    - stated in a citable document (give ``source``/``revision``)
      estimated    - derived or inferred by the user; explain in ``notes``
      illustrative - placeholder, not real hardware data (the default)

    ``uncertainty_pct`` is the relative 1-sigma uncertainty of the values, in
    percent; ``None`` means the uncertainty is unknown, not zero.
    """

    quality: str = "illustrative"
    source: str = ""
    revision: str = ""
    uncertainty_pct: float | None = None
    units: str = "SI (kg, N, s, Pa, m, deg)"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.quality not in QUALITIES:
            raise ValueError(f"quality must be one of {', '.join(QUALITIES)}")
        if self.quality in TRACEABLE_QUALITIES and not self.source.strip():
            raise ValueError(f"{self.quality} data requires a source citation")
        if self.uncertainty_pct is not None and (
            not math.isfinite(self.uncertainty_pct) or self.uncertainty_pct < 0.0
        ):
            raise ValueError("uncertainty_pct must be a finite nonnegative number")

    @property
    def is_traceable(self) -> bool:
        return self.quality in TRACEABLE_QUALITIES
