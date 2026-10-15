from typing import get_args

import pytest

from pydantic_super_model import SuperModelMixin, collect_annotated_fields, find_annotation_match
from tests.models.metadata import ColumnOptions, NestedAliasedColumnField, SearchOptions, TaggedColumnField
from tests.models.plain_user import PlainParameterAliasConfig
from tests.models.user import DerivedColumnConfig, ParametrizedColumnConfig


class TestNamedAliases:
    """Test that field lookup sees through named and specialized type aliases."""

    @pytest.mark.parametrize(
        ("field", "names"),
        [
            pytest.param("column", ["alias"], id="optional-alias"),
            pytest.param("generic", ["generic"], id="specialized"),
            pytest.param("identity", ["argument"], id="identity"),
            pytest.param("nested_identity", ["nested-argument"], id="nested-identity"),
            pytest.param("forwarded", ["forwarded-argument"], id="forwarded"),
            pytest.param("nested_forwarded", ["nested-forwarded"], id="nested-forwarded"),
            pytest.param("scoped", [], id="free-parameter"),
        ],
    )
    def test_field_metadata_through_alias(
        self,
        aliased_model: type[SuperModelMixin],
        field: str,
        names: list[str],
    ) -> None:
        """Test that metadata reached through an alias is returned for the argument it binds."""

        assert [item.name for item in aliased_model.field_metadata(field, ColumnOptions)] == names

    def test_alias_layers_outermost_first(self, aliased_model: type[SuperModelMixin]) -> None:
        """Test that metadata around a named alias comes before the metadata inside it."""

        search, column = aliased_model.field_metadata("column", SearchOptions, ColumnOptions)

        assert (search.weight, column.name) == (3, "alias")

    @pytest.mark.parametrize(
        ("field", "name", "weight"),
        [
            pytest.param("tagged", "tagged-argument", 9, id="generic-body"),
            pytest.param("forwarded_tagged", "forwarded-tagged-argument", 11, id="forwarded-body"),
        ],
    )
    def test_argument_metadata_flattens_first(
        self,
        aliased_model: type[SuperModelMixin],
        field: str,
        name: str,
        weight: int,
    ) -> None:
        """Test that a bound argument's metadata comes first, as Python flattens nested Annotated."""

        column, search = aliased_model.field_metadata(field, SearchOptions, ColumnOptions)

        assert (column.name, search.weight) == (name, weight)

    @pytest.mark.parametrize("field", ["identity", "forwarded", "nested_forwarded"])
    def test_bound_argument_matches_its_type(self, aliased_model: type[SuperModelMixin], field: str) -> None:
        """Test that a bound alias argument matches the concrete type written for it."""

        assert collect_annotated_fields(aliased_model, str)[field].annotation is str

    @pytest.mark.parametrize(
        ("field", "name"),
        [
            pytest.param("column", "alias", id="optional-alias"),
            pytest.param("identity", "argument", id="identity"),
            pytest.param("nested_forwarded", "nested-forwarded", id="nested-forwarded"),
        ],
    )
    def test_matched_metadata_through_alias(
        self,
        aliased_model: type[SuperModelMixin],
        field: str,
        name: str,
    ) -> None:
        """Test that a metadata class lookup matches metadata inside an alias."""

        assert collect_annotated_fields(aliased_model, ColumnOptions)[field].matched_metadata[0].name == name

    def test_alias_lookup_keeps_alias_identity(self, aliased_model: type[SuperModelMixin]) -> None:
        """Test that looking up an alias returns the alias itself with every nested metadata item."""

        field = collect_annotated_fields(aliased_model, NestedAliasedColumnField)["column"]

        assert field.annotation is NestedAliasedColumnField
        assert [type(item) for item in field.metadata] == [SearchOptions, ColumnOptions]

    def test_selects_every_aliased_field(self, aliased_model: type[SuperModelMixin]) -> None:
        """Test that class-level field selection sees metadata inside every alias."""

        assert aliased_model.field_names_with_metadata(ColumnOptions) == frozenset(
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

    @pytest.mark.parametrize(
        ("field", "value", "name"),
        [
            pytest.param("identity", "value", "argument", id="identity"),
            pytest.param("forwarded", "forwarded", "forwarded-argument", id="forwarded"),
            pytest.param("nested_forwarded", "nested-forwarded", "nested-forwarded", id="nested-forwarded"),
        ],
    )
    def test_instance_lookup_keeps_values(
        self,
        aliased_model: type[SuperModelMixin],
        field: str,
        value: str,
        name: str,
    ) -> None:
        """Test that an instance lookup through an alias returns the field value and its metadata."""

        annotated_field = aliased_model().get_annotated_fields(ColumnOptions)[field]

        assert (annotated_field.value, annotated_field.matched_metadata[0].name) == (value, name)

    def test_parameters_after_variadic_bind_trailing_arguments(self) -> None:
        """Test that parameters after a variadic one bind the trailing arguments."""

        column, search = PlainParameterAliasConfig.field_metadata("trailing", SearchOptions, ColumnOptions)

        assert (column.name, search.weight) == ("trailing-argument", 13)

    def test_unwritten_argument_binds_default(self) -> None:
        """Test that a type parameter without an argument binds its declared default."""

        column, search = PlainParameterAliasConfig.field_metadata("defaulted", SearchOptions, ColumnOptions)

        assert (column.name, search.weight) == ("default-argument", 19)

    def test_match_substitutes_bound_arguments(self) -> None:
        """Test that a match inside a generic alias reports its arguments substituted."""

        match = find_annotation_match(TaggedColumnField, (SearchOptions,))

        assert match is not None
        assert get_args(match.annotation)[0] is str
        assert [type(item) for item in match.metadata] == [ColumnOptions, SearchOptions]

    @pytest.mark.parametrize(
        ("model", "name"),
        [
            pytest.param(ParametrizedColumnConfig, "model-argument", id="parametrized"),
            pytest.param(DerivedColumnConfig, "derived-argument", id="derived"),
        ],
    )
    def test_parametrized_model_binds_its_arguments(
        self,
        model: type[SuperModelMixin],
        name: str,
    ) -> None:
        """Test that a parametrized Pydantic model's arguments reach alias fields in every lookup."""

        class_field = collect_annotated_fields(model, ColumnOptions)["column"]
        instance_field = model(column="x").get_annotated_fields(ColumnOptions)["column"]

        assert [item.name for item in model.field_metadata("column", ColumnOptions)] == [name]
        assert class_field.matched_metadata[0].name == name
        assert (instance_field.value, instance_field.matched_metadata[0].name) == ("x", name)
