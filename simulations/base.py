from abc import ABC, abstractmethod

class Simulation(ABC):

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def step(self):
        pass

    @abstractmethod
    def render(self, canvas, camera):
        pass