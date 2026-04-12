from typing import Annotated

import pytest

from pydantic_super_model import SuperModelMixin, FieldNotImplemented
from tests.helpers import _field_info
from tests.models.plain_user import (
    PlainThemeConfig,
    PlainUser,
    PlainUserNoAnnotations,
    PlainUserWithAnnotatedAnnotation,
    PlainUserWithType,
    PlainUserWithUnionAnnotation,
    PrimaryKey,
    ThemeColorField,
    _PrimaryKeyAnnotation,
    _ThemeColorOptions,
)


class TestPlainClassAnnotatedFields:
    """Test annotated field discovery on plain Python classes."""

    def test_returns_matching_annotated_fields(self) -> None:
        """Return fields that carry the requested annotation."""

        user = PlainUser(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation)}

    def test_returns_empty_when_model_has_no_annotations(self) -> None:
        """Return an empty mapping when no matching annotations exist."""

        user = PlainUserNoAnnotations(id=1, name="John Doe")

        assert not user.get_annotated_fields(PrimaryKey)

    def test_returns_empty_when_no_annotations_are_requested(self) -> None:
        """Return an empty mapping when no annotations are provided."""

        user = PlainUser(id=1, name="John Doe")

        assert not user.get_annotated_fields()

    def test_matches_annotations_with_union_types(self) -> None:
        """Match annotations nested inside union type hints."""

        user = PlainUserWithUnionAnnotation(id=1, name="John Doe")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_matches_annotations_with_direct_annotated_types(self) -> None:
        """Match annotations defined directly with Annotated."""

        user = PlainUserWithAnnotatedAnnotation(id=1, name="John Doe")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_includes_none_values_on_plain_classes(self) -> None:
        """Include None values since plain classes have no model_fields_set tracking."""

        class _PlainOptionalPK(SuperModelMixin):
            id: PrimaryKey | None
            name: str

            def __init__(self, name: str, id: PrimaryKey | None = None) -> None:
                self.id = id
                self.name = name

        user = _PlainOptionalPK(name="A")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(None, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_includes_falsy_non_none_values(self) -> None:
        """Include falsy values when the field is present."""

        user = PlainUser(id=0, name="Zero")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(0, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_matches_metadata_annotation_classes(self) -> None:
        """Match using the metadata annotation class itself."""

        user = PlainUser(id=1, name="John Doe")

        assert user.get_annotated_fields(_PrimaryKeyAnnotation) == {
            "id": _field_info(
                1,
                PrimaryKey,
                _PrimaryKeyAnnotation,
                matched_metadata=(_PrimaryKeyAnnotation,),
            )
        }

    def test_returns_metadata_instances_for_class_based_lookup(self) -> None:
        """Return metadata instances when matching by metadata class."""

        theme = PlainThemeConfig(accent_color="#7dd3fc", theme_name="Aurora")

        annotated_fields = theme.get_annotated_fields(_ThemeColorOptions)
        field_info = annotated_fields["accent_color"]
        matched_metadata = field_info.matched_metadata

        assert field_info == _field_info(
            "#7dd3fc",
            ThemeColorField,
            "theme_color",
            matched_metadata[0],
            matched_metadata=matched_metadata,
        )
        assert len(matched_metadata) == 1
        assert isinstance(matched_metadata[0], _ThemeColorOptions)
        assert matched_metadata[0].palette == "northern-lights"
        assert matched_metadata[0].allow_gradients is True


class TestPlainClassAnnotatedFieldValue:
    """Test access to the first matching annotated field on plain classes."""

    def test_returns_first_matching_field_info(self) -> None:
        """Return the first matching annotated field info."""

        user = PlainUser(id=7, name="Jane")

        assert user.get_annotated_field_value(PrimaryKey) == _field_info(
            7,
            PrimaryKey,
            _PrimaryKeyAnnotation,
        )

    def test_raises_when_no_matching_field_exists(self) -> None:
        """Raise when no field is annotated with the requested annotation."""

        user = PlainUserNoAnnotations(id=1, name="X")

        with pytest.raises(ValueError):
            user.get_annotated_field_value(PrimaryKey)

    def test_returns_none_when_undefined_is_allowed(self) -> None:
        """Return None when no field exists and undefined values are allowed."""

        user = PlainUserNoAnnotations(id=1, name="X")

        assert user.get_annotated_field_value(PrimaryKey, allow_undefined=True) is None

    def test_returns_field_info_for_falsy_values(self) -> None:
        """Return field info for falsy values other than None."""

        user = PlainUser(id=0, name="Zero")

        assert user.get_annotated_field_value(PrimaryKey) == _field_info(
            0,
            PrimaryKey,
            _PrimaryKeyAnnotation,
        )


class TestPlainClassGenerics:
    """Test generic type introspection on plain classes."""

    def test_returns_the_concrete_generic_type(self) -> None:
        """Return the concrete generic type supplied at instantiation."""

        user_with_type = PlainUserWithType[int](id=1, name="John Doe")

        assert user_with_type.get_type() is int

    def test_returns_none_when_no_generic_type_is_present(self) -> None:
        """Return None for classes without a concrete generic parameter."""

        user = PlainUser(id=1, name="John Doe")

        assert user.get_type() is None


class TestPlainClassValidation:
    """Test manual validation for FieldNotImplemented on plain classes."""

    def test_raises_when_not_implemented_field_is_present(self) -> None:
        """Raise when validate_not_implemented_fields is called with a set field."""

        class _PlainNotImplemented(SuperModelMixin):
            test_field: Annotated[int, FieldNotImplemented]
            name: str

            def __init__(self, test_field: int, name: str) -> None:
                self.test_field = test_field
                self.name = name

        model = _PlainNotImplemented(test_field=1, name="x")

        with pytest.raises(NotImplementedError):
            model.validate_not_implemented_fields()

    def test_passes_when_no_not_implemented_fields_exist(self) -> None:
        """Pass validation when no FieldNotImplemented annotations exist."""

        user = PlainUser(id=1, name="test")

        user.validate_not_implemented_fields()
