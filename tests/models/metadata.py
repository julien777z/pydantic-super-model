from typing import Annotated


class PrimaryKeyAnnotation:
    """Metadata marking a field as a primary key."""


class ThemeColorOptions:
    """Metadata options describing theme color rendering."""

    def __init__(self, *, palette: str, allow_gradients: bool) -> None:
        self.palette = palette
        self.allow_gradients = allow_gradients


class ColumnOptions:
    """Metadata options identifying a column."""

    def __init__(self, *, name: str) -> None:
        self.name = name


class SearchOptions:
    """Metadata options describing search behavior."""

    def __init__(self, *, weight: int) -> None:
        self.weight = weight


PrimaryKey = Annotated[int, PrimaryKeyAnnotation]
ThemeColorField = Annotated[
    str,
    "theme_color",
    ThemeColorOptions(palette="northern-lights", allow_gradients=True),
]
BareColumnField = Annotated[str, ColumnOptions(name="bare"), SearchOptions(weight=1)]
OptionalColumnField = Annotated[str, ColumnOptions(name="optional")]
NestedColumnField = Annotated[Annotated[str, ColumnOptions(name="inner")], ColumnOptions(name="outer")]
