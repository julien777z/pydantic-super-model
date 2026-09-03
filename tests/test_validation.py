from typing import Annotated

import pytest
from pydantic import PrivateAttr

from pydantic_super_model import FieldNotImplemented, SuperModelPydanticMixin


class TestNotImplementedValidation:
    """Test that fields marked as not implemented are rejected."""

    def test_raises_when_not_implemented_field_is_present(self) -> None:
        """Test that it raises when a not-implemented field is provided."""

        class _ModelWithNotImplementedField(SuperModelPydanticMixin):
            """Model with a required not-implemented field."""

            test_field: Annotated[int, FieldNotImplemented]
            name: str

        with pytest.raises(NotImplementedError):
            _ModelWithNotImplementedField(test_field=1, name="x")

    def test_allows_unset_optional_not_implemented_fields(self) -> None:
        """Test that it allows optional not-implemented fields when they remain unset."""

        class _OptionalNotImplementedFieldModel(SuperModelPydanticMixin):
            """Model with an optional not-implemented field."""

            test_field: Annotated[int | None, FieldNotImplemented] = None
            name: str

        model = _OptionalNotImplementedFieldModel(name="x")

        assert model.name == "x"

    def test_raises_for_falsy_non_none_values(self) -> None:
        """Test that it raises for falsy values when the field is still present."""

        class _ModelWithZeroValue(SuperModelPydanticMixin):
            """Model with a falsy not-implemented field value."""

            test_field: Annotated[int, FieldNotImplemented]
            name: str

        with pytest.raises(NotImplementedError):
            _ModelWithZeroValue(test_field=0, name="z")

    def test_raises_for_not_implemented_private_attributes(self) -> None:
        """Test that it raises when a private attribute is marked not implemented."""

        class _ModelWithNotImplementedPrivateAttribute(SuperModelPydanticMixin):
            """Model with a not-implemented private attribute."""

            _test_field: Annotated[int, FieldNotImplemented] = PrivateAttr(default=1)

        with pytest.raises(NotImplementedError):
            _ModelWithNotImplementedPrivateAttribute()
