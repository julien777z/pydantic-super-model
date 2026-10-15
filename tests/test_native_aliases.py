import pytest

from pydantic_super_model import SuperModelMixin, collect_annotated_fields, find_annotation_match
from tests.models.metadata import ColumnOptions
from tests.models.native_aliases import (
    NativeAliasConfig,
    NativeColumnField,
    PlainNativeAliasConfig,
    PlainRecursiveAliasConfig,
    Recursive,
)


class TestNativeAliases:
    """Test that field lookup sees through aliases declared with the type statement."""

    @pytest.mark.parametrize("model", [NativeAliasConfig, PlainNativeAliasConfig], ids=["pydantic", "plain"])
    @pytest.mark.parametrize(
        ("field", "names"),
        [
            pytest.param("column", ["native"], id="optional"),
            pytest.param("tagged", ["native-tagged", "native-argument"], id="generic"),
        ],
    )
    def test_field_metadata_through_alias(
        self,
        model: type[SuperModelMixin],
        field: str,
        names: list[str],
    ) -> None:
        """Test that metadata inside a type statement alias is returned in order."""

        assert [item.name for item in model.field_metadata(field, ColumnOptions)] == names

    def test_alias_lookup_keeps_alias_identity(self) -> None:
        """Test that looking up a type statement alias returns the alias with its metadata."""

        field = collect_annotated_fields(NativeAliasConfig, NativeColumnField)["column"]

        assert field.annotation is NativeColumnField
        assert [item.name for item in field.metadata] == ["native"]

    @pytest.mark.parametrize(
        ("field", "names"),
        [
            pytest.param("recursive", ["recursive"], id="self-reference"),
            pytest.param("expanding", ["expanding", "expanding"], id="generic-expansion"),
            pytest.param("loop", [], id="captured-argument"),
        ],
    )
    def test_recursive_alias_terminates(self, field: str, names: list[str]) -> None:
        """Test that metadata lookup stops at an alias already being expanded."""

        metadata = PlainRecursiveAliasConfig.field_metadata(field, ColumnOptions)

        assert [item.name for item in metadata] == names

    def test_recursive_alias_without_match(self) -> None:
        """Test that a recursive alias carrying no requested annotation matches nothing."""

        assert find_annotation_match(Recursive, ("missing-marker",)) is None
