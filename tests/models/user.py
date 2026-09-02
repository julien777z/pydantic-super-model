from typing import Annotated, Generic, TypeVar

from pydantic_super_model import SuperModelPydanticMixin
from tests.models.metadata import (
    BareColumnField,
    NestedColumnField,
    OptionalColumnField,
    PrimaryKey,
    PrimaryKeyAnnotation,
    ThemeColorField,
)

GenericType = TypeVar("GenericType", bound=int)


class User(SuperModelPydanticMixin):
    """User test model."""

    id: PrimaryKey
    name: str


class UserNoAnnotations(SuperModelPydanticMixin):
    """User test model without annotations."""

    id: int
    name: str


class UserWithUnionAnnotation(SuperModelPydanticMixin):
    """User test model with union."""

    id: PrimaryKey | str
    name: str


class UserWithAnnotatedAnnotation(SuperModelPydanticMixin):
    """User test model with annotated annotation."""

    id: Annotated[int, PrimaryKeyAnnotation]
    name: str


class UserWithType(SuperModelPydanticMixin, Generic[GenericType]):
    """User test model with type."""

    id: GenericType
    name: str


class ThemeConfig(SuperModelPydanticMixin):
    """Theme config model with instance-based metadata annotation."""

    accent_color: ThemeColorField
    theme_name: str


class ColumnConfig(SuperModelPydanticMixin):
    """Column config model covering every annotation shape carrying metadata."""

    bare: BareColumnField
    optional: OptionalColumnField | None
    nested: NestedColumnField
    unannotated: str
