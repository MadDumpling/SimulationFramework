import numpy as np

from viewport.orbit_camera import MAX_PITCH, MIN_PITCH, OrbitCamera


def test_eye_is_distance_from_target():
    camera = OrbitCamera()
    camera.target = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    camera.distance = 7.0

    assert abs(np.linalg.norm(camera.eye - camera.target) - 7.0) < 1e-4


def test_pitch_is_clamped():
    camera = OrbitCamera()

    camera.orbit(0.0, 1e6)
    assert camera.pitch == MAX_PITCH
    camera.orbit(0.0, -1e9)
    assert camera.pitch == MIN_PITCH


def test_zoom_respects_limits():
    camera = OrbitCamera()
    camera.min_distance, camera.max_distance = 2.0, 30.0

    camera.zoom(1000)
    assert camera.distance == 2.0
    camera.zoom(-1000)
    assert camera.distance == 30.0


def test_frame_fits_bounding_sphere():
    camera = OrbitCamera()
    camera.frame(np.array([0.0, 5.0, 0.0]), 5.0)

    assert camera.distance > 5.0
    np.testing.assert_allclose(camera.target, (0, 5, 0))


def test_target_projects_to_screen_centre():
    camera = OrbitCamera()
    camera.target = np.array([0.0, 4.0, 0.0], dtype=np.float32)
    clip = camera.view_projection(16 / 9) @ np.array([0.0, 4.0, 0.0, 1.0])

    np.testing.assert_allclose(clip[:2] / clip[3], (0.0, 0.0), atol=1e-5)
    assert 0.0 < clip[2] / clip[3] < 1.0


def test_pan_moves_target_perpendicular_to_view():
    camera = OrbitCamera()
    before = camera.target.copy()
    forward = camera.target - camera.eye

    camera.pan(50.0, 20.0, 720.0)

    moved = camera.target - before
    assert np.linalg.norm(moved) > 0.0
    assert abs(np.dot(moved, forward)) < 1e-4
