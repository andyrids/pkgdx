"""Fixture package."""


class Animal:
    """An animal."""

    def speak(self) -> str:
        """Make a sound."""
        return "..."


class Dog(Animal):
    """A dog."""

    def speak(self) -> str:
        """Bark."""
        return "WOOF!"
