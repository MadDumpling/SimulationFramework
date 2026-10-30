from collections import deque


class MetricsManager:

    def __init__(
        self,
        history=300,
    ):

        self.history = history

        self.metrics = {}

    def register(
        self,
        name,
    ):

        self.metrics[name] = deque(
            maxlen=self.history
        )

    def record(
        self,
        name,
        value,
    ):

        if name in self.metrics:

            self.metrics[name].append(
                float(value)
            )

    def get(
        self,
        name,
    ):

        return list(
            self.metrics[name]
        )