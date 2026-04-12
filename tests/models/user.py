from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel

from pydantic_super_model import SuperModelMixin


class _PrimaryKeyAnnotation:
    pass


class _ThemeColorOptions:
    def __init__(self, *, palette: str, allow_gradients: bool) -> None:
        self.palette = palette
        self.allow_gradients = allow_gradients


PrimaryKey = Annotated[int, _PrimaryKeyAnnotation]
ThemeColorField = Annotated[
    str,
    "theme_color",
    _ThemeColorOptions(palette="northern-lights", allow_gradients=True),
]
GenericType = TypeVar("GenericType", bound=int)


class User(SuperModelMixin, BaseModel):
    """User test model."""

    id: PrimaryKey
    name: str


class UserNoAnnotations(SuperModelMixin, BaseModel):
    """User test model without annotations."""

    id: int
    name: str


class UserWithUnionAnnotation(SuperModelMixin, BaseModel):
    """User test model with union."""

    id: PrimaryKey | str
    name: str


class UserWithAnnotatedAnnotation(SuperModelMixin, BaseModel):
    """User test model with annotated annotation."""

    id: Annotated[int, _PrimaryKeyAnnotation]
    name: str


class UserWithType(SuperModelMixin, BaseModel, Generic[GenericType]):
    """User test model with type."""

    id: GenericType
    name: str


class ThemeConfig(SuperModelMixin, BaseModel):
    """Theme config model with instance-based metadata annotation."""

    accent_color: ThemeColorField
    theme_name: str
