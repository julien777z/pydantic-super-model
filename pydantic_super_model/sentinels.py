from enum import Enum, auto


class Missing(Enum):
    """Mark a value that an object does not hold."""

    ATTRIBUTE = auto()
