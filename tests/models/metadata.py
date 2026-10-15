from typing import Annotated

from typing_extensions import TypeAliasType, TypeVar, TypeVarTuple


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


AliasValues = TypeVarTuple("AliasValues")
TrailingAlias = TypeAliasType(
    "TrailingAlias", Annotated[AliasValue, SearchOptions(weight=13)], type_params=(AliasValues, AliasValue)
)
TrailingColumnField = TrailingAlias[str, bytes, Annotated[str, ColumnOptions(name="trailing-argument")]]

FreeParameterAlias = TypeAliasType("FreeParameterAlias", Annotated[AliasValue, SearchOptions(weight=17)])
ScopedAlias = TypeAliasType("ScopedAlias", FreeParameterAlias, type_params=(AliasValue,))
ScopedColumnField = ScopedAlias[Annotated[str, ColumnOptions(name="caller-argument")]]

DefaultedValue = TypeVar("DefaultedValue", default=Annotated[str, ColumnOptions(name="default-argument")])
DefaultedAlias = TypeAliasType(
    "DefaultedAlias", Annotated[DefaultedValue, SearchOptions(weight=19)], type_params=(DefaultedValue,)
)
