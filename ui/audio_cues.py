"""Short synthesized demo sounds played with the host operating system."""

from array import array
import math
import shutil
import subprocess
import sys
import tempfile
import wave

SAMPLE_RATE = 22_050
CUES = ("takeoff", "success", "failure")


class AudioCues:
    def __init__(self):
        self.enabled = True
        self._directory = tempfile.TemporaryDirectory(prefix="spacecraft-audio-")
        self._paths = {
            cue: f"{self._directory.name}/{cue}.wav"
            for cue in CUES
        }
        self._generated = False
        self._process = None
        self._player = self._find_player()
        self._error = None

    @staticmethod
    def _find_player():
        if sys.platform == "darwin":
            executable = shutil.which("afplay")
            return (executable,) if executable else None
        if sys.platform.startswith("win"):
            return ("winsound",)
        for name, arguments in (("paplay", ()), ("aplay", ("-q",))):
            executable = shutil.which(name)
            if executable:
                return (executable, *arguments)
        return None

    @property
    def status_message(self):
        if self._error:
            return self._error
        if self._player is None:
            return "Demo audio unavailable: no supported system audio player was found."
        return (
            "Demo sounds enabled: takeoff, then a success or failure cue."
            if self.enabled
            else "Demo sounds are muted."
        )

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        if self.enabled:
            self._error = None
        if not self.enabled:
            self.stop()

    def play(self, cue: str) -> str | None:
        if cue not in self._paths:
            raise ValueError(f"Unknown audio cue: {cue}")
        if not self.enabled:
            return None
        if self._player is None:
            return self.status_message
        try:
            self._generate_cues()
            self.stop()
            if self._player[0] == "winsound":
                import winsound

                winsound.PlaySound(
                    self._paths[cue],
                    winsound.SND_FILENAME | winsound.SND_ASYNC,
                )
            else:
                self._process = subprocess.Popen(
                    (*self._player, self._paths[cue]),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except (OSError, RuntimeError) as error:
            self._error = f"Demo audio could not play: {error}"
            return self._error
        return None

    def stop(self) -> None:
        if self._player is not None and self._player[0] == "winsound":
            import winsound

            winsound.PlaySound(None, 0)
        process, self._process = self._process, None
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except ProcessLookupError:
                return
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def close(self) -> None:
        self.stop()
        self._directory.cleanup()

    def _generate_cues(self) -> None:
        if self._generated:
            return
        _write_wave(self._paths["takeoff"], "takeoff")
        _write_wave(self._paths["success"], "success")
        _write_wave(self._paths["failure"], "failure")
        self._generated = True


def _write_wave(path: str, cue: str) -> None:
    duration = {"takeoff": 2.8, "success": 1.4, "failure": 1.3}[cue]
    samples = array("h")
    total = int(SAMPLE_RATE * duration)
    for index in range(total):
        time_s = index / SAMPLE_RATE
        if cue == "takeoff":
            envelope = min(1.0, time_s * 4.0) * min(1.0, (duration - time_s) * 1.8)
            base = 62.0 + 34.0 * time_s / duration
            value = (
                math.sin(2.0 * math.pi * base * time_s)
                + 0.34 * math.sin(2.0 * math.pi * base * 2.03 * time_s)
                + 0.18 * math.sin(2.0 * math.pi * 27.0 * time_s)
            )
            value *= envelope * (0.62 + 0.12 * math.sin(time_s * 17.0))
        else:
            notes = (
                (523.25, 659.25, 783.99, 1046.5)
                if cue == "success"
                else (392.0, 311.13, 233.08)
            )
            note_duration = duration / len(notes)
            note_index = min(int(time_s / note_duration), len(notes) - 1)
            local_time = time_s - note_index * note_duration
            frequency = notes[note_index]
            envelope = min(1.0, local_time * 16.0) * min(
                1.0,
                (note_duration - local_time) * 4.0,
            )
            value = (
                math.sin(2.0 * math.pi * frequency * time_s)
                + 0.18 * math.sin(2.0 * math.pi * frequency * 2.0 * time_s)
            ) * envelope * 0.55
        samples.append(int(max(-1.0, min(1.0, value)) * 32767))

    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(path, "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(SAMPLE_RATE)
        audio_file.writeframes(samples.tobytes())
