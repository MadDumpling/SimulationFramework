# parameters.py

class Parameter:
    def __init__(
        self,
        name,
        value,
        min_value,
        max_value,
    ):
        self.name = name
        self.value = value
        self.min = min_value
        self.max = max_value