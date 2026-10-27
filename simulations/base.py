# base.py
from abc import ABC, abstractmethod

class Simulation(ABC):

    name = "Unknown"
    author = "Unknown"
    version = "0.1"

    def __init__(self):
        self.parameters = {}

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def step(self, dt):
        pass

    @abstractmethod
    def render(self, canvas, camera):
        pass

    def serialize(self):
        return {}

    def deserialize(self, state):
        pass
