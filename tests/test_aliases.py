import pytest

from pydantic_super_model import SuperModelMixin, collect_annotated_fields
from tests.models.metadata import ColumnOptions, NestedAliasedColumnField, SearchOptions
from tests.models.plain_user import PlainVariadicAliasConfig


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

    @pytest.mark.parametrize(
        ("field", "weight", "name"),
        [
            pytest.param("column", 3, "alias", id="nested-alias"),
            pytest.param("tagged", 9, "tagged-argument", id="generic-body"),
            pytest.param("forwarded_tagged", 11, "forwarded-tagged-argument", id="forwarded-body"),
        ],
    )
    def test_declaration_metadata_precedes_argument(
        self,
        aliased_model: type[SuperModelMixin],
        field: str,
        weight: int,
        name: str,
    ) -> None:
        """Test that an alias body's metadata comes before the metadata of its bound argument."""

        search, column = aliased_model.field_metadata(field, SearchOptions, ColumnOptions)

        assert (search.weight, column.name) == (weight, name)

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

        search, column = PlainVariadicAliasConfig.field_metadata("trailing", SearchOptions, ColumnOptions)

        assert (search.weight, column.name) == (13, "trailing-argument")
