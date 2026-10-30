"""Spacecraft assembly model, intentionally independent of the UI framework."""

from dataclasses import dataclass, field

from .components import Component


@dataclass
class Spacecraft:
    name: str = "Untitled spacecraft"
    components: list[Component] = field(default_factory=list)
    # Editor-only normalized canvas positions, keyed by component ID.
    layout: dict[str, tuple[float, float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("spacecraft name must not be empty")

    def add_component(self, component: Component) -> None:
        if not isinstance(component, Component):
            raise TypeError("component must be a spacecraft Component")
        if any(existing.id == component.id for existing in self.components):
            raise ValueError(f"Component id already exists: {component.id}")
        self.components.append(component)

    def remove_component(self, component_id: str) -> bool:
        for index, component in enumerate(self.components):
            if component.id == component_id:
                del self.components[index]
                self.layout.pop(component_id, None)
                return True
        return False

    def get_component(self, component_id: str) -> Component | None:
        return next(
            (part for part in self.components if part.id == component_id),
            None,
        )
