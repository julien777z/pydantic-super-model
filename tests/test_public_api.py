import importlib

import pytest

from pydantic_super_model import AnnotatedFieldInfo, FieldNotImplemented, PydanticMixin, SuperModelMixin


class TestPublicApi:
    """Test the package-level public API."""

    def test_exports_the_supported_root_symbols(self) -> None:
        """Export the supported symbols from the package root."""

        package = importlib.import_module("pydantic_super_model")

        assert package.SuperModelMixin is SuperModelMixin
        assert package.PydanticMixin is PydanticMixin
        assert package.AnnotatedFieldInfo is AnnotatedFieldInfo
        assert package.FieldNotImplemented is FieldNotImplemented
        assert package.__all__ == ["AnnotatedFieldInfo", "FieldNotImplemented", "PydanticMixin", "SuperModelMixin"]

    def test_legacy_model_module_is_no_longer_importable(self) -> None:
        """Raise when importing the removed legacy module path."""

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("pydantic_super_model.model")

    def test_legacy_base_module_is_no_longer_importable(self) -> None:
        """Raise when importing the removed base module path."""

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("pydantic_super_model.base")
