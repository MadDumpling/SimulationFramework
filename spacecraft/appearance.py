"""Serializable, UI-independent spacecraft visual customization options."""

from dataclasses import dataclass

PAINT_SCHEMES = {
    "Orbital White": {
        "primary": (0.82, 0.86, 0.91),
        "accent": (0.18, 0.32, 0.52),
        "trim": (0.86, 0.48, 0.18),
    },
    "Deep Space": {
        "primary": (0.12, 0.17, 0.27),
        "accent": (0.28, 0.48, 0.72),
        "trim": (0.95, 0.64, 0.24),
    },
    "Lunar Gold": {
        "primary": (0.72, 0.62, 0.38),
        "accent": (0.20, 0.28, 0.38),
        "trim": (0.92, 0.78, 0.48),
    },
    "Arctic Survey": {
        "primary": (0.74, 0.87, 0.90),
        "accent": (0.10, 0.42, 0.52),
        "trim": (0.96, 0.46, 0.24),
    },
    "Forest Research": {
        "primary": (0.25, 0.42, 0.34),
        "accent": (0.82, 0.76, 0.58),
        "trim": (0.91, 0.55, 0.22),
    },
}

NATIONAL_FLAGS = (
    "None",
    "United States",
    "Canada",
    "Japan",
    "India",
    "France",
    "Germany",
    "Italy",
    "United Kingdom",
    "China",
)


@dataclass
class SpacecraftAppearance:
    paint_scheme: str = "Orbital White"
    national_flag: str = "United States"

    def __post_init__(self) -> None:
        if self.paint_scheme not in PAINT_SCHEMES:
            raise ValueError(f"Unknown paint scheme: {self.paint_scheme}")
        if self.national_flag not in NATIONAL_FLAGS:
            raise ValueError(f"Unknown national flag: {self.national_flag}")
