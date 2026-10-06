import typing
from typing import Annotated, Generic, TypeVar

from pydantic_super_model import SuperModelPydanticMixin
from tests.models.metadata import (
    BareColumnField,
    ColumnOptions,
    ForwardedColumnField,
    ForwardedTaggedColumnField,
    GenericAliasedColumnField,
    IdentityColumnField,
    NestedAliasedColumnField,
    NestedColumnField,
    NestedForwardedColumnField,
    NestedIdentityColumnField,
    OptionalColumnField,
    PrimaryKey,
    PrimaryKeyAnnotation,
    SearchOptions,
    TaggedColumnField,
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


class AliasedColumnConfig(SuperModelPydanticMixin):
    """Model with native named and specialized annotation aliases."""

    column: NestedAliasedColumnField | None = None
    generic: GenericAliasedColumnField[int] = 1
    identity: IdentityColumnField = "value"
    nested_identity: NestedIdentityColumnField = "nested"
    tagged: TaggedColumnField = "tagged"
    forwarded: ForwardedColumnField = "forwarded"
    forwarded_tagged: ForwardedTaggedColumnField = "forwarded-tagged"
    nested_forwarded: NestedForwardedColumnField = "nested-forwarded"


def create_native_column_model() -> type[SuperModelPydanticMixin]:
    """Declare a test model using the interpreter's native named alias class."""

    native_alias = typing.TypeAliasType("NativeColumn", Annotated[str, ColumnOptions(name="native")])

    class NativeColumn(SuperModelPydanticMixin):
        """Model carrying a standard-library named alias."""

        column: native_alias | None = None

    return NativeColumn


class InheritedColumnBase(SuperModelPydanticMixin):
    """Base model declaring inherited column metadata."""

    identifier: Annotated[str, ColumnOptions(name="identifier")]


class InheritedColumnChild(InheritedColumnBase):
    """Child model declaring additional column metadata."""

    label: Annotated[str, ColumnOptions(name="label")]


class UnionColumnConfig(SuperModelPydanticMixin):
    """Model whose union members carry different metadata types."""

    column: Annotated[int, ColumnOptions(name="numeric")] | Annotated[str, SearchOptions(weight=1)]
