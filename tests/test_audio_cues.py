import wave

import pytest

from ui import audio_cues
from ui.audio_cues import AudioCues


def test_audio_cues_generate_playable_local_wav_files(tmp_path, monkeypatch):
    class CompletedProcess:
        def poll(self):
            return 0

        def terminate(self):
            pass

    launched = []
    monkeypatch.setattr(
        audio_cues.subprocess,
        "Popen",
        lambda command, **kwargs: launched.append((command, kwargs)) or CompletedProcess(),
    )
    cues = AudioCues()
    cues._player = ("fake-audio-player",)
    cues._paths = {cue: str(tmp_path / f"{cue}.wav") for cue in audio_cues.CUES}

    try:
        assert cues.play("takeoff") is None
        assert launched[0][0] == ("fake-audio-player", cues._paths["takeoff"])
        for path in cues._paths.values():
            with wave.open(path, "rb") as sound:
                assert sound.getnchannels() == 1
                assert sound.getsampwidth() == 2
                assert sound.getframerate() == audio_cues.SAMPLE_RATE
                assert sound.getnframes() > 0
    finally:
        cues.close()


def test_audio_cues_respect_mute_and_reject_unknown_sounds(monkeypatch):
    cues = AudioCues()
    cues._player = ("fake-audio-player",)
    cues.set_enabled(False)
    monkeypatch.setattr(
        audio_cues.subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail("muted audio must not start a player"),
    )

    try:
        assert cues.play("takeoff") is None
        with pytest.raises(ValueError, match="Unknown audio cue"):
            cues.play("unknown")
    finally:
        cues.close()
