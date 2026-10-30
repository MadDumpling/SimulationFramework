from collections import deque


class Metric:

    def __init__(
        self,
        name,
        value=0.0,
        graph=False,
        history=300,
    ):

        self.name = name

        self.value = value

        self.graph = graph

        self.history = deque(
            maxlen=history
        )

    def update(
        self,
        value,
    ):

        self.value = value

        if self.graph:

            self.history.append(
                float(value)
            )