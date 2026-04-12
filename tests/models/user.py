from typing import Annotated, Generic, TypeVar

from pydantic_super_model import PydanticMixin


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


class User(PydanticMixin):
    """User test model."""

    id: PrimaryKey
    name: str


class UserNoAnnotations(PydanticMixin):
    """User test model without annotations."""

    id: int
    name: str


class UserWithUnionAnnotation(PydanticMixin):
    """User test model with union."""

    id: PrimaryKey | str
    name: str


class UserWithAnnotatedAnnotation(PydanticMixin):
    """User test model with annotated annotation."""

    id: Annotated[int, _PrimaryKeyAnnotation]
    name: str


class UserWithType(PydanticMixin, Generic[GenericType]):
    """User test model with type."""

    id: GenericType
    name: str


class ThemeConfig(PydanticMixin):
    """Theme config model with instance-based metadata annotation."""

    accent_color: ThemeColorField
    theme_name: str
