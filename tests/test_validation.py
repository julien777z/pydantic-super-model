from typing import Annotated

import pytest

from pydantic_super_model import FieldNotImplemented, PydanticMixin


class TestNotImplementedValidation:
    """Test validation for fields marked as not implemented."""

    def test_raises_when_not_implemented_field_is_present(self) -> None:
        """Raise when a not-implemented field is provided."""

        class _ModelWithNotImplementedField(PydanticMixin):
            """Model with a required not-implemented field."""

            test_field: Annotated[int, FieldNotImplemented]
            name: str

        with pytest.raises(NotImplementedError):
            _ModelWithNotImplementedField(test_field=1, name="x")

    def test_allows_unset_optional_not_implemented_fields(self) -> None:
        """Allow optional not-implemented fields when they remain unset."""

        class _OptionalNotImplementedFieldModel(PydanticMixin):
            """Model with an optional not-implemented field."""

            test_field: Annotated[int | None, FieldNotImplemented] = None
            name: str

        model = _OptionalNotImplementedFieldModel(name="x")

        assert model.name == "x"

    def test_raises_for_falsy_non_none_values(self) -> None:
        """Raise for falsy values when the field is still present."""

        class _ModelWithZeroValue(PydanticMixin):
            """Model with a falsy not-implemented field value."""

            test_field: Annotated[int, FieldNotImplemented]
            name: str

        with pytest.raises(NotImplementedError):
            _ModelWithZeroValue(test_field=0, name="z")
