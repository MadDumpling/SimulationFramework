"""4x4 transform helpers (row-major, column vectors: p' = M @ p). Y is up."""

import math

import numpy as np




def translate(x: float, y: float, z: float) -> np.ndarray:
    matrix = np.eye(4, dtype=np.float32)
    matrix[:3, 3] = (x, y, z)
    return matrix


def scale(x: float, y: float, z: float) -> np.ndarray:
    return np.diag([x, y, z, 1.0]).astype(np.float32)


def rotate_y(angle: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    matrix = np.eye(4, dtype=np.float32)
    matrix[0, 0], matrix[0, 2] = c, s
    matrix[2, 0], matrix[2, 2] = -s, c
    return matrix


def rotate_z(angle: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    matrix = np.eye(4, dtype=np.float32)
    matrix[0, 0], matrix[0, 1] = c, -s
    matrix[1, 0], matrix[1, 1] = s, c
    return matrix


def rotation_between(source, target, fraction: float = 1.0) -> np.ndarray:
    """Rotation taking direction ``source`` toward ``target`` (shortest arc).

    ``fraction`` in [0, 1] rotates only part of the way (0 = identity).
    """
    a = np.asarray(source, dtype=np.float64)
    b = np.asarray(target, dtype=np.float64)
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    axis = np.cross(a, b)
    sine = np.linalg.norm(axis)
    cosine = float(np.dot(a, b))
    matrix = np.eye(4, dtype=np.float32)
    if sine < 1e-9:
        if cosine > 0.0:
            return matrix
        # Opposite directions: half turn about any axis perpendicular to a.
        axis = np.cross(a, (1.0, 0.0, 0.0))
        if np.linalg.norm(axis) < 1e-6:
            axis = np.cross(a, (0.0, 0.0, 1.0))
        angle = math.pi
    else:
        angle = math.atan2(sine, cosine)
    angle *= float(np.clip(fraction, 0.0, 1.0))
    axis = axis / np.linalg.norm(axis)
    x, y, z = axis
    k = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    matrix[:3, :3] = np.eye(3) + math.sin(angle) * k + (1.0 - math.cos(angle)) * (k @ k)
    return matrix


def rotate_x(angle: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    matrix = np.eye(4, dtype=np.float32)
    matrix[1, 1], matrix[1, 2] = c, -s
    matrix[2, 1], matrix[2, 2] = s, c
    return matrix


def euler_xyz_degrees(rx: float, ry: float, rz: float) -> np.ndarray:
    """Rotation applying X first, then Y, then Z (angles in degrees)."""
    return (
        rotate_z(math.radians(rz)) @ rotate_y(math.radians(ry)) @ rotate_x(math.radians(rx))
    ).astype(np.float32)


def rotation_part(matrix: np.ndarray) -> np.ndarray:
    """The 3x3 rotation (assumes no scale)."""
    return np.asarray(matrix, dtype=np.float64)[:3, :3]


def transform_point(matrix: np.ndarray, point) -> np.ndarray:
    return (np.asarray(matrix, dtype=np.float64) @ np.array([point[0], point[1], point[2], 1.0]))[:3]


def transform_direction(matrix: np.ndarray, direction) -> np.ndarray:
    return rotation_part(matrix) @ np.asarray(direction, dtype=np.float64)
