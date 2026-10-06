import sys
from typing import get_args

import pytest

from pydantic_super_model import SuperModelMixin, SuperModelPydanticMixin
from pydantic_super_model.annotation_lookup import collect_annotated_fields
from pydantic_super_model.models import BoundAnnotation
from tests.models.annotated_field_info import build_field_info
from tests.models.metadata import (
    ColumnOptions,
    NestedAliasedColumnField,
    PrimaryKey,
    PrimaryKeyAnnotation,
    SearchOptions,
    create_native_recursive_aliases,
)
from tests.models.plain_user import (
    PlainAliasedColumnConfig,
    PlainClassVariableConfig,
    PlainColumnConfig,
    PlainUser,
)
from tests.models.user import (
    AliasedColumnConfig,
    ColumnConfig,
    InheritedColumnChild,
    UnionColumnConfig,
    User,
    create_native_column_model,
)


class TestClassMetadata:
    """Test class-level metadata, field selection and native annotation lookup."""

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_metadata_of_a_bare_annotated_field(self, model: type[SuperModelMixin]) -> None:
        """Test that metadata hoisted onto a bare Annotated field is returned."""

        assert [item.name for item in model.field_metadata("bare", ColumnOptions)] == ["bare"]

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_metadata_nested_in_an_optional_union(self, model: type[SuperModelMixin]) -> None:
        """Test that metadata nested inside an optional union member is returned."""

        assert [item.name for item in model.field_metadata("optional", ColumnOptions)] == ["optional"]

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_every_metadata_instance_of_a_nested_annotated_field(
        self,
        model: type[SuperModelMixin],
    ) -> None:
        """Test that each metadata instance of a nested Annotated field is returned in order."""

        assert [item.name for item in model.field_metadata("nested", ColumnOptions)] == ["inner", "outer"]

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_empty_for_a_field_without_metadata(self, model: type[SuperModelMixin]) -> None:
        """Test that a field carrying no metadata returns an empty tuple."""

        assert model.field_metadata("unannotated", ColumnOptions) == ()

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_excludes_metadata_of_an_unrequested_type(self, model: type[SuperModelMixin]) -> None:
        """Test that metadata of a type that was not requested is excluded."""

        assert [type(item) for item in model.field_metadata("bare", SearchOptions)] == [SearchOptions]

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_metadata_of_every_requested_type(self, model: type[SuperModelMixin]) -> None:
        """Test that metadata of each requested type is returned in declaration order."""

        metadata = model.field_metadata("bare", ColumnOptions, SearchOptions)

        assert [type(item) for item in metadata] == [ColumnOptions, SearchOptions]

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_field_metadata_returns_empty_when_no_metadata_types_are_requested(
        self,
        model: type[SuperModelMixin],
    ) -> None:
        """Test that requesting no metadata types returns an empty tuple."""

        assert model.field_metadata("bare") == ()

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    @pytest.mark.parametrize(
        "metadata_types",
        [pytest.param((ColumnOptions,), id="with-types"), pytest.param((), id="without-types")],
    )
    def test_raises_for_an_undeclared_field(
        self,
        model: type[SuperModelMixin],
        metadata_types: tuple[type[object], ...],
    ) -> None:
        """Test that an undeclared field raises whether or not metadata types are requested."""

        with pytest.raises(KeyError):
            model.field_metadata("missing", *metadata_types)

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_the_first_metadata_instance(self, model: type[SuperModelMixin]) -> None:
        """Test that the first metadata instance carried by the field is returned."""

        first = model.first_field_metadata("nested", ColumnOptions)

        assert first is not None
        assert first.name == "inner"

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_none_for_a_field_without_metadata(self, model: type[SuperModelMixin]) -> None:
        """Test that a field carrying no metadata of the requested type returns None."""

        assert model.first_field_metadata("unannotated", ColumnOptions) is None

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_every_field_carrying_the_metadata_type(self, model: type[SuperModelMixin]) -> None:
        """Test that every field whose annotation carries the requested type is returned."""

        assert model.field_names_with_metadata(ColumnOptions) == frozenset({"bare", "optional", "nested"})

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_only_the_fields_carrying_a_narrower_metadata_type(
        self,
        model: type[SuperModelMixin],
    ) -> None:
        """Test that only fields carrying the requested type are returned when other metadata exists."""

        assert model.field_names_with_metadata(SearchOptions) == frozenset({"bare"})

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_returns_every_field_carrying_any_requested_type(self, model: type[SuperModelMixin]) -> None:
        """Test that fields carrying any of several requested types are returned."""

        assert model.field_names_with_metadata(ColumnOptions, SearchOptions) == frozenset(
            {"bare", "optional", "nested"}
        )

    @pytest.mark.parametrize("model", [ColumnConfig, PlainColumnConfig])
    def test_field_names_with_metadata_returns_empty_when_no_metadata_types_are_requested(
        self,
        model: type[SuperModelMixin],
    ) -> None:
        """Test that requesting no metadata types returns an empty set."""

        assert model.field_names_with_metadata() == frozenset()

    def test_collects_pydantic_class_fields_without_values(self) -> None:
        """Test that a Pydantic model class yields its annotated fields with no values."""

        assert collect_annotated_fields(User, PrimaryKey) == {
            "id": build_field_info(None, PrimaryKey, PrimaryKeyAnnotation)
        }

    def test_collects_plain_class_fields_without_values(self) -> None:
        """Test that a plain class yields its annotated fields with no values."""

        assert collect_annotated_fields(PlainUser, PrimaryKey) == {
            "id": build_field_info(None, PrimaryKey, PrimaryKeyAnnotation)
        }

    def test_collects_the_same_fields_as_an_instance(self) -> None:
        """Test that a class yields the same fields as one of its instances."""

        instance_fields = collect_annotated_fields(User(id=1, name="John Doe"), PrimaryKey)
        class_fields = collect_annotated_fields(User, PrimaryKey)

        assert list(class_fields) == list(instance_fields)
        assert class_fields["id"] == instance_fields["id"]._replace(value=None)

    def test_returns_empty_when_no_annotations_are_requested(self) -> None:
        """Test that requesting no annotations from a class returns an empty mapping."""

        assert not collect_annotated_fields(User)

    def test_resolves_metadata_declared_on_a_base_class(self) -> None:
        """Test that metadata for fields a subclass inherits is resolved."""

        assert InheritedColumnChild.field_names_with_metadata(ColumnOptions) == frozenset(
            {"identifier", "label"}
        )
        assert [item.name for item in InheritedColumnChild.field_metadata("identifier", ColumnOptions)] == [
            "identifier"
        ]

    def test_returns_metadata_from_every_union_member(self) -> None:
        """Test that a union carrying two metadata types reports both of them."""

        metadata = UnionColumnConfig.field_metadata("column", ColumnOptions, SearchOptions)

        assert [type(item) for item in metadata] == [ColumnOptions, SearchOptions]

    def test_omits_class_variables_from_a_plain_class(self) -> None:
        """Test that a plain class's class variable is not treated as a declared field."""

        assert PlainClassVariableConfig.field_names_with_metadata(ColumnOptions) == frozenset({"column"})

        with pytest.raises(KeyError):
            PlainClassVariableConfig.field_metadata("DEFAULT_COLUMN", ColumnOptions)

    @pytest.mark.skipif(sys.version_info < (3, 12), reason="Native TypeAliasType starts in Python 3.12")
    def test_native_alias_exposes_metadata(self) -> None:
        """Test the actual standard-library alias class carries discoverable metadata."""

        model = create_native_column_model()
        native_alias = get_args(model.model_fields["column"].annotation)[0]

        assert [item.name for item in model.field_metadata("column", ColumnOptions)] == ["native"]
        field = collect_annotated_fields(model, native_alias)["column"]
        assert field.annotation is native_alias
        assert field.metadata[0].name == "native"

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_nested_optional_alias_preserves_outer_and_inner_metadata(
        self, model: type[SuperModelMixin]
    ) -> None:
        """Test metadata order across nested named and optional aliases."""

        metadata = model.field_metadata("column", SearchOptions, ColumnOptions)
        assert [type(item) for item in metadata] == [SearchOptions, ColumnOptions]
        assert metadata[0].weight == 3
        assert metadata[1].name == "alias"

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_specialized_generic_alias_exposes_its_metadata(self, model: type[SuperModelMixin]) -> None:
        """Test a specialized alias retains its declaration metadata."""

        assert [item.name for item in model.field_metadata("generic", ColumnOptions)] == ["generic"]

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_alias_lookup_retains_alias_identity_and_metadata(self, model: type[SuperModelMixin]) -> None:
        """Test explicit alias lookup preserves its identity and full metadata."""

        field = collect_annotated_fields(model, NestedAliasedColumnField)["column"]
        assert field.annotation is NestedAliasedColumnField
        assert [type(item) for item in field.metadata] == [SearchOptions, ColumnOptions]

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_metadata_lookup_descends_into_named_alias(self, model: type[SuperModelMixin]) -> None:
        """Test matching a metadata class traverses alias boundaries."""

        field = collect_annotated_fields(model, ColumnOptions)["column"]
        assert field.matched_metadata[0].name == "alias"

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_every_union_arm_remains_visible(self, model: type[SuperModelMixin]) -> None:
        """Test named aliases remain visible to class-level field selection."""

        assert model.field_names_with_metadata(ColumnOptions) == frozenset(
            {
                "column",
                "generic",
                "identity",
                "nested_identity",
                "tagged",
                "forwarded",
                "forwarded_tagged",
                "nested_forwarded",
            }
        )

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_bound_type_argument_metadata_remains_visible(self, model: type[SuperModelMixin]) -> None:
        """Test annotation metadata supplied through a generic identity alias."""

        assert [item.name for item in model.field_metadata("identity", ColumnOptions)] == ["argument"]
        field = collect_annotated_fields(model, ColumnOptions)["identity"]
        assert field.matched_metadata[0].name == "argument"

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_nested_parameter_bindings_retain_the_actual_argument(self, model: type[SuperModelMixin]) -> None:
        """Test nested specializations resolve through every alias parameter binding."""

        assert [item.name for item in model.field_metadata("nested_identity", ColumnOptions)] == [
            "nested-argument"
        ]

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_bound_alias_matches_the_concrete_argument_type(
        self, model: type[AliasedColumnConfig] | type[PlainAliasedColumnConfig]
    ) -> None:
        """Test primitive annotation selection uses the actual specialized argument."""

        field = collect_annotated_fields(model, str)["identity"]
        assert field.annotation is str

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_argument_metadata_lookup_retains_instance_values(
        self, model: type[AliasedColumnConfig] | type[PlainAliasedColumnConfig]
    ) -> None:
        """Test plain and Pydantic instances expose bound-argument metadata and values."""

        instance = model(
            column="column",
            generic=3,
            identity="value",
            nested_identity="nested",
            tagged="tagged",
            forwarded="forwarded",
            forwarded_tagged="forwarded-tagged",
            nested_forwarded="nested-forwarded",
        )
        field = instance.get_annotated_fields(ColumnOptions)["identity"]
        assert field.value == "value"
        assert field.matched_metadata[0].name == "argument"
        forwarded = instance.get_annotated_fields(ColumnOptions)["forwarded"]
        assert forwarded.value == "forwarded"
        assert forwarded.matched_metadata[0].name == "forwarded-argument"
        nested_forwarded = instance.get_annotated_fields(ColumnOptions)["nested_forwarded"]
        assert nested_forwarded.value == "nested-forwarded"
        assert nested_forwarded.matched_metadata[0].name == "nested-forwarded"

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_generic_declaration_metadata_precedes_argument_metadata(
        self, model: type[SuperModelMixin]
    ) -> None:
        """Test an Annotated generic body keeps outer metadata before its bound argument."""

        metadata = model.field_metadata("tagged", SearchOptions, ColumnOptions)
        assert [type(item) for item in metadata] == [SearchOptions, ColumnOptions]
        assert metadata[0].weight == 9
        assert metadata[1].name == "tagged-argument"

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_forwarded_shared_parameter_retains_concrete_metadata(self, model: type[SuperModelMixin]) -> None:
        """Test forwarded aliases reusing one TypeVar retain the original concrete argument."""

        assert [item.name for item in model.field_metadata("forwarded", ColumnOptions)] == [
            "forwarded-argument"
        ]
        assert collect_annotated_fields(model, str)["forwarded"].annotation is str

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_forwarded_expression_keeps_its_lexical_environment(self, model: type[SuperModelMixin]) -> None:
        """Test a nested argument expression retains outer metadata and its incoming parameter."""

        metadata = model.field_metadata("forwarded_tagged", SearchOptions, ColumnOptions)
        assert [type(item) for item in metadata] == [SearchOptions, ColumnOptions]
        assert metadata[0].weight == 11
        assert metadata[1].name == "forwarded-tagged-argument"

    @pytest.mark.parametrize("model", [AliasedColumnConfig, PlainAliasedColumnConfig])
    def test_nested_forwarded_alias_retains_finite_argument_context(
        self, model: type[SuperModelMixin]
    ) -> None:
        """Test nested forwarded specializations can revisit a body in distinct captured arguments."""

        assert [item.name for item in model.field_metadata("nested_forwarded", ColumnOptions)] == [
            "nested-forwarded"
        ]
        assert (
            collect_annotated_fields(model, ColumnOptions)["nested_forwarded"].matched_metadata[0].name
            == "nested-forwarded"
        )
        assert collect_annotated_fields(model, str)["nested_forwarded"].annotation is str

    @pytest.mark.skipif(
        sys.version_info < (3, 12), reason="Native recursive type aliases start in Python 3.12"
    )
    def test_native_recursive_declarations_terminate(self) -> None:
        """Test self recursion, generic expansion and recursive captured arguments terminate."""

        for alias in create_native_recursive_aliases():
            bound = BoundAnnotation(alias)
            assert bound.find_match(("missing-marker",)) is None
            bound.metadata()
