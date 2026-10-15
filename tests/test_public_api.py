import importlib

import pytest

from pydantic_super_model import (
    AnnotatedFieldInfo,
    FieldNotImplemented,
    SuperModelMixin,
    SuperModelPydanticMixin,
    collect_annotated_fields,
    find_annotation_match,
)


class TestPublicApi:
    """Test that the package-level public API exports the supported symbols."""

    def test_exports_the_supported_root_symbols(self) -> None:
        """Test that it exports the supported symbols from the package root."""

        package = importlib.import_module("pydantic_super_model")

        assert package.SuperModelMixin is SuperModelMixin
        assert package.SuperModelPydanticMixin is SuperModelPydanticMixin
        assert package.AnnotatedFieldInfo is AnnotatedFieldInfo
        assert package.FieldNotImplemented is FieldNotImplemented
        assert package.collect_annotated_fields is collect_annotated_fields
        assert package.find_annotation_match is find_annotation_match
        assert package.__all__ == [
            "AnnotatedFieldInfo",
            "FieldNotImplemented",
            "SuperModelPydanticMixin",
            "SuperModelMixin",
            "collect_annotated_fields",
            "find_annotation_match",
        ]

    def test_legacy_model_module_is_no_longer_importable(self) -> None:
        """Test that it raises when importing the removed legacy module path."""

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("pydantic_super_model.model")

    def test_legacy_base_module_is_no_longer_importable(self) -> None:
        """Test that it raises when importing the removed base module path."""

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("pydantic_super_model.base")
