
import pytest

from spacecraft.analysis import (
    SpacecraftAnalysis,
    MissionProfile,
    assess_mission
)

def test_spacecraft_can_complete_mission():
    spacecraft = SpacecraftAnalysis(
        delta_v=15000,
        twr=2.0
    )

    mission = MissionProfile(
        id="test",
        name="Test Mission",
        required_delta_v=10000
    )

    result = assess_mission(spacecraft, mission)

    assert result.achievable == True
    assert result.delta_v_margin == 5000
