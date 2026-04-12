from typing import Annotated, Generic, TypeVar

from pydantic_super_model import AnnotationsMixin


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


class PlainUser(AnnotationsMixin):
    """Plain-class user test model."""

    id: PrimaryKey
    name: str

    def __init__(self, id: PrimaryKey, name: str) -> None:
        self.id = id
        self.name = name


class PlainUserNoAnnotations(AnnotationsMixin):
    """Plain-class user test model without annotations."""

    id: int
    name: str

    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name


class PlainUserWithUnionAnnotation(AnnotationsMixin):
    """Plain-class user test model with union."""

    id: PrimaryKey | str
    name: str

    def __init__(self, id: PrimaryKey | str, name: str) -> None:
        self.id = id
        self.name = name


class PlainUserWithAnnotatedAnnotation(AnnotationsMixin):
    """Plain-class user test model with annotated annotation."""

    id: Annotated[int, _PrimaryKeyAnnotation]
    name: str

    def __init__(self, id: Annotated[int, _PrimaryKeyAnnotation], name: str) -> None:
        self.id = id
        self.name = name


class PlainUserWithType(AnnotationsMixin, Generic[GenericType]):
    """Plain-class user test model with type."""

    id: GenericType
    name: str

    def __init__(self, id: GenericType, name: str) -> None:
        self.id = id
        self.name = name


class PlainThemeConfig(AnnotationsMixin):
    """Plain-class theme config model with instance-based metadata annotation."""

    accent_color: ThemeColorField
    theme_name: str

    def __init__(self, accent_color: ThemeColorField, theme_name: str) -> None:
        self.accent_color = accent_color
        self.theme_name = theme_name
