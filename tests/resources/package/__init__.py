"""Fixture package."""


class Animal:
    """An animal."""

    def speak(self) -> str:
        """Makes a sound."""
        return "..."


class Dog(Animal):
    """A dog."""

    def speak(self) -> str:
        """Barks."""
        return "WOOF!"
