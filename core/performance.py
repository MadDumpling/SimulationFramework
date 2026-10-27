import time


class PerformanceMonitor:

    def __init__(self):

        self.last_time = (
            time.perf_counter()
        )

        self.fps = 0.0

        self.frame_time = 0.0

    def update(self):

        current = (
            time.perf_counter()
        )

        delta = (
            current
            - self.last_time
        )

        self.last_time = current

        self.frame_time = (
            delta * 1000.0
        )

        if delta > 0.0:

            self.fps = (
                1.0 / delta
            )