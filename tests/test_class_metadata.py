from typing import Annotated, Final

import pytest

from pydantic_super_model import SuperModelMixin, SuperModelPydanticMixin
from pydantic_super_model.annotation_lookup import collect_annotated_fields
from tests.helpers import build_field_info
from tests.models.metadata import ColumnOptions, PrimaryKey, PrimaryKeyAnnotation, SearchOptions
from tests.models.plain_user import PlainColumnConfig, PlainUser
from tests.models.user import ColumnConfig, User

COLUMN_CONFIGS: Final = [ColumnConfig, PlainColumnConfig]
COLUMN_CONFIG_IDS: Final = ["pydantic", "plain"]


@pytest.mark.parametrize("model", COLUMN_CONFIGS, ids=COLUMN_CONFIG_IDS)
class TestFieldMetadata:
    """Test that class-level field metadata resolves for every annotation shape."""

    def test_returns_metadata_of_a_bare_annotated_field(self, model: type[SuperModelMixin]) -> None:
        """Test that metadata hoisted onto a bare Annotated field is returned."""

        assert [item.name for item in model.field_metadata("bare", ColumnOptions)] == ["bare"]

    def test_returns_metadata_nested_in_an_optional_union(self, model: type[SuperModelMixin]) -> None:
        """Test that metadata nested inside an optional union member is returned."""

        assert [item.name for item in model.field_metadata("optional", ColumnOptions)] == ["optional"]

    def test_returns_every_metadata_instance_of_a_nested_annotated_field(
        self,
        model: type[SuperModelMixin],
    ) -> None:
        """Test that each metadata instance of a nested Annotated field is returned in order."""

        assert [item.name for item in model.field_metadata("nested", ColumnOptions)] == ["inner", "outer"]

    def test_returns_empty_for_a_field_without_metadata(self, model: type[SuperModelMixin]) -> None:
        """Test that a field carrying no metadata returns an empty tuple."""

        assert model.field_metadata("unannotated", ColumnOptions) == ()

    def test_excludes_metadata_of_an_unrequested_type(self, model: type[SuperModelMixin]) -> None:
        """Test that metadata of a type that was not requested is excluded."""

        assert [type(item) for item in model.field_metadata("bare", SearchOptions)] == [SearchOptions]

    def test_returns_metadata_of_every_requested_type(self, model: type[SuperModelMixin]) -> None:
        """Test that metadata of each requested type is returned in declaration order."""

        metadata = model.field_metadata("bare", ColumnOptions, SearchOptions)

        assert [type(item) for item in metadata] == [ColumnOptions, SearchOptions]

    def test_returns_empty_when_no_metadata_types_are_requested(
        self,
        model: type[SuperModelMixin],
    ) -> None:
        """Test that requesting no metadata types returns an empty tuple."""

        assert model.field_metadata("bare") == ()

    def test_raises_for_an_undeclared_field(self, model: type[SuperModelMixin]) -> None:
        """Test that requesting metadata for an undeclared field raises."""

        with pytest.raises(KeyError):
            model.field_metadata("missing", ColumnOptions)


@pytest.mark.parametrize("model", COLUMN_CONFIGS, ids=COLUMN_CONFIG_IDS)
class TestFirstFieldMetadata:
    """Test that class-level single metadata resolution returns the first match."""

    def test_returns_the_first_metadata_instance(self, model: type[SuperModelMixin]) -> None:
        """Test that the first metadata instance carried by the field is returned."""

        first = model.first_field_metadata("nested", ColumnOptions)

        assert first is not None
        assert first.name == "inner"

    def test_returns_none_for_a_field_without_metadata(self, model: type[SuperModelMixin]) -> None:
        """Test that a field carrying no metadata of the requested type returns None."""

        assert model.first_field_metadata("unannotated", ColumnOptions) is None


@pytest.mark.parametrize("model", COLUMN_CONFIGS, ids=COLUMN_CONFIG_IDS)
class TestFieldNamesWithMetadata:
    """Test that class-level field name resolution selects fields by metadata type."""

    def test_returns_every_field_carrying_the_metadata_type(self, model: type[SuperModelMixin]) -> None:
        """Test that every field whose annotation carries the requested type is returned."""

        assert model.field_names_with_metadata(ColumnOptions) == frozenset({"bare", "optional", "nested"})

    def test_returns_only_the_fields_carrying_a_narrower_metadata_type(
        self,
        model: type[SuperModelMixin],
    ) -> None:
        """Test that only fields carrying the requested type are returned when other metadata exists."""

        assert model.field_names_with_metadata(SearchOptions) == frozenset({"bare"})

    def test_returns_every_field_carrying_any_requested_type(self, model: type[SuperModelMixin]) -> None:
        """Test that fields carrying any of several requested types are returned."""

        assert model.field_names_with_metadata(ColumnOptions, SearchOptions) == frozenset(
            {"bare", "optional", "nested"}
        )

    def test_returns_empty_when_no_metadata_types_are_requested(
        self,
        model: type[SuperModelMixin],
    ) -> None:
        """Test that requesting no metadata types returns an empty set."""

        assert model.field_names_with_metadata() == frozenset()


class TestClassLevelAnnotatedFields:
    """Test that annotated fields are collected from a class as well as an instance."""

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


class TestInheritedClassMetadata:
    """Test that class-level metadata resolves across inheritance."""

    def test_resolves_metadata_declared_on_a_base_class(self) -> None:
        """Test that metadata for fields a subclass inherits is resolved."""

        class _Base(SuperModelPydanticMixin):
            """Base model declaring an annotated field."""

            identifier: Annotated[str, ColumnOptions(name="identifier")]

        class _Child(_Base):
            """Child model declaring a second annotated field."""

            label: Annotated[str, ColumnOptions(name="label")]

        assert _Child.field_names_with_metadata(ColumnOptions) == frozenset({"identifier", "label"})
        assert [item.name for item in _Child.field_metadata("identifier", ColumnOptions)] == ["identifier"]
