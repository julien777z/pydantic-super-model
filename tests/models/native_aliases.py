from typing import Annotated

from pydantic_super_model import SuperModelMixin, SuperModelPydanticMixin
from tests.models.metadata import ColumnOptions

type NativeColumnField = Annotated[str, ColumnOptions(name="native")]
type NativeTagged[T] = Annotated[T, ColumnOptions(name="native-tagged")]
type NativeTaggedColumnField = NativeTagged[Annotated[str, ColumnOptions(name="native-argument")]]

type Recursive = Annotated[Recursive | int, ColumnOptions(name="recursive")]
type Expanding[T] = Annotated[T, ColumnOptions(name="expanding")] | Expanding[list[T]]
type Identity[T] = T
type AliasLoop = Identity[AliasLoop]


class NativeAliasConfig(SuperModelPydanticMixin):
    """Model declaring fields with the type statement."""

    column: NativeColumnField | None = None
    tagged: NativeTaggedColumnField = "tagged"


class PlainNativeAliasConfig(SuperModelMixin):
    """Plain model declaring fields with the type statement."""

    column: NativeColumnField | None = None
    tagged: NativeTaggedColumnField = "tagged"


class PlainRecursiveAliasConfig(SuperModelMixin):
    """Plain model whose fields use recursive type statements."""

    recursive: Recursive
    expanding: Expanding[int]
    loop: AliasLoop
