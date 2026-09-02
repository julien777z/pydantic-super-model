from typing import Annotated, Generic, TypeVar

from pydantic_super_model import SuperModelMixin
from tests.models.metadata import (
    BareColumnField,
    NestedColumnField,
    OptionalColumnField,
    PrimaryKey,
    PrimaryKeyAnnotation,
    ThemeColorField,
)

GenericType = TypeVar("GenericType", bound=int)


class PlainUser(SuperModelMixin):
    """Plain-class user test model."""

    id: PrimaryKey
    name: str

    def __init__(self, id: PrimaryKey, name: str) -> None:
        self.id = id
        self.name = name


class PlainUserNoAnnotations(SuperModelMixin):
    """Plain-class user test model without annotations."""

    id: int
    name: str

    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name


class PlainUserWithUnionAnnotation(SuperModelMixin):
    """Plain-class user test model with union."""

    id: PrimaryKey | str
    name: str

    def __init__(self, id: PrimaryKey | str, name: str) -> None:
        self.id = id
        self.name = name


class PlainUserWithAnnotatedAnnotation(SuperModelMixin):
    """Plain-class user test model with annotated annotation."""

    id: Annotated[int, PrimaryKeyAnnotation]
    name: str

    def __init__(self, id: Annotated[int, PrimaryKeyAnnotation], name: str) -> None:
        self.id = id
        self.name = name


class PlainUserWithType(SuperModelMixin, Generic[GenericType]):
    """Plain-class user test model with type."""

    id: GenericType
    name: str

    def __init__(self, id: GenericType, name: str) -> None:
        self.id = id
        self.name = name


class PlainThemeConfig(SuperModelMixin):
    """Plain-class theme config model with instance-based metadata annotation."""

    accent_color: ThemeColorField
    theme_name: str

    def __init__(self, accent_color: ThemeColorField, theme_name: str) -> None:
        self.accent_color = accent_color
        self.theme_name = theme_name


class PlainColumnConfig(SuperModelMixin):
    """Plain-class column config model covering every annotation shape carrying metadata."""

    bare: BareColumnField
    optional: OptionalColumnField | None
    nested: NestedColumnField
    unannotated: str
