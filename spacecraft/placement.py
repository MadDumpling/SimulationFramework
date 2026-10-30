"""How a part is attached to the vehicle (Kerbal-style attach nodes, no numpy).

A part either has no ``Placement`` (it is arranged by the automatic stack layout, as
in older designs) or a ``Placement`` that snaps one of its own nodes onto a node of a
parent part, then applies a manual offset and rotation. A part with no parent is a
root: ``offset`` is then the world position of its centre.

Nodes (see ``spacecraft.assembly`` for the geometry):
  top, bottom  the ends of a cylindrical part (or an engine's mount, which is its top)
  side         anywhere on the curved surface, at ``angle_deg`` around the part axis
  mount        the single attachment point of a radially mounted part (leg, thruster...)
"""

from dataclasses import dataclass
import math

NODE_TOP = "top"
NODE_BOTTOM = "bottom"
NODE_SIDE = "side"
NODE_MOUNT = "mount"
NODE_NAMES = (NODE_TOP, NODE_BOTTOM, NODE_SIDE, NODE_MOUNT)


def _vec3(name: str, value) -> tuple[float, float, float]:
    try:
        result = tuple(float(v) for v in value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be 3 numbers") from error
    if len(result) != 3 or not all(math.isfinite(v) for v in result):
        raise ValueError(f"{name} must be 3 finite numbers")
    return result


@dataclass
class Placement:
    parent_id: str | None = None  # None: a root part
    parent_node: str = NODE_TOP  # node on the parent this part snaps to
    node: str = NODE_BOTTOM  # node on this part that does the snapping
    angle_deg: float = 0.0  # azimuth around the parent axis, for side attachment
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0)  # m, in the parent frame
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)  # extra Euler XYZ
    symmetry_group: str | None = None  # parts created together by symmetry share this

    def __post_init__(self) -> None:
        for name, value in (("parent_node", self.parent_node), ("node", self.node)):
            if value not in NODE_NAMES:
                raise ValueError(f"{name} must be one of {', '.join(NODE_NAMES)}")
        if not math.isfinite(self.angle_deg):
            raise ValueError("angle_deg must be finite")
        self.offset = _vec3("offset", self.offset)
        self.rotation_deg = _vec3("rotation_deg", self.rotation_deg)
        if self.parent_id is not None and not str(self.parent_id).strip():
            raise ValueError("parent_id must not be empty")
