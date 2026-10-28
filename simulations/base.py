# base.py

from abc import (
    ABC,
    abstractmethod,
)


class Simulation(ABC):

    name = "Unknown"

    author = "Unknown"

    version = "0.1"

    description = ""

    def __init__(self):

        self.parameters = {}

        self.metrics = {}

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def step(self):
        pass

    @abstractmethod
    def render(
        self,
        canvas,
        camera,
    ):
        pass

    def serialize(self):

        return {
            name: parameter.value
            for (
                name,
                parameter,
            ) in self.parameters.items()
        }

    def deserialize(
        self,
        data,
    ):

        for (
            name,
            value,
        ) in data.items():

            if (
                name
                in self.parameters
            ):

                self.parameters[
                    name
                ].value = value