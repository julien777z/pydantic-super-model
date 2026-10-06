from typing import Annotated, TypeVar

from typing_extensions import TypeAliasType


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


AliasedColumnField = TypeAliasType("AliasedColumnField", Annotated[str, ColumnOptions(name="alias")])
NestedAliasedColumnField = TypeAliasType(
    "NestedAliasedColumnField", Annotated[AliasedColumnField, SearchOptions(weight=3)]
)
AliasValue = TypeVar("AliasValue")
GenericAliasedColumnField = TypeAliasType(
    "GenericAliasedColumnField",
    Annotated[AliasValue, ColumnOptions(name="generic")],
    type_params=(AliasValue,),
)

IdentityAlias = TypeAliasType("IdentityAlias", AliasValue, type_params=(AliasValue,))
IdentityColumnField = IdentityAlias[Annotated[str, ColumnOptions(name="argument")]]
NestedIdentityColumnField = IdentityAlias[
    IdentityAlias[Annotated[str, ColumnOptions(name="nested-argument")]]
]

TaggedAlias = TypeAliasType(
    "TaggedAlias", Annotated[AliasValue, SearchOptions(weight=9)], type_params=(AliasValue,)
)
TaggedColumnField = TaggedAlias[Annotated[str, ColumnOptions(name="tagged-argument")]]

ForwardedAlias = TypeAliasType("ForwardedAlias", IdentityAlias[AliasValue], type_params=(AliasValue,))
ForwardedColumnField = ForwardedAlias[Annotated[str, ColumnOptions(name="forwarded-argument")]]
ForwardedTaggedAlias = TypeAliasType(
    "ForwardedTaggedAlias",
    IdentityAlias[Annotated[AliasValue, SearchOptions(weight=11)]],
    type_params=(AliasValue,),
)
ForwardedTaggedColumnField = ForwardedTaggedAlias[
    Annotated[str, ColumnOptions(name="forwarded-tagged-argument")]
]

NestedForwardedColumnField = ForwardedAlias[
    ForwardedAlias[Annotated[str, ColumnOptions(name="nested-forwarded")]]
]


def create_native_recursive_aliases() -> tuple[object, ...]:
    """Declare actual lazy recursive aliases using the interpreter's native syntax."""

    namespace: dict[str, object] = {"Annotated": Annotated, "ColumnOptions": ColumnOptions}
    exec(
        "type Recursive = Annotated[Recursive | int, ColumnOptions(name='recursive')]\n"
        "type Expanding[T] = Annotated[T, ColumnOptions(name='expanding')] | Expanding[list[T]]\n"
        "ExpandingInteger = Expanding[int]\n"
        "type Identity[T] = T\n"
        "type AliasLoop = Identity[AliasLoop]\n",
        namespace,
    )

    return namespace["Recursive"], namespace["ExpandingInteger"], namespace["AliasLoop"]
