from typing import Annotated

import pytest

from pydantic_super_model import FieldNotImplemented, SuperModelMixin
from tests.models.annotated_field_info import build_field_info
from tests.models.metadata import (
    PrimaryKey,
    PrimaryKeyAnnotation,
    ThemeColorField,
    ThemeColorOptions,
)
from tests.models.plain_user import (
    PlainThemeConfig,
    PlainUser,
    PlainUserNoAnnotations,
    PlainUserWithAnnotatedAnnotation,
    PlainUserWithType,
    PlainUserWithUnionAnnotation,
)


class TestPlainClassAnnotatedFields:
    """Test that annotated field discovery works on plain Python classes."""

    def test_returns_matching_annotated_fields(self) -> None:
        """Test that it returns fields that carry the requested annotation."""

        user = PlainUser(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": build_field_info(1, PrimaryKey, PrimaryKeyAnnotation)}

    def test_returns_empty_when_model_has_no_annotations(self) -> None:
        """Test that it returns an empty mapping when no matching annotations exist."""

        user = PlainUserNoAnnotations(id=1, name="John Doe")

        assert not user.get_annotated_fields(PrimaryKey)

    def test_returns_empty_when_no_annotations_are_requested(self) -> None:
        """Test that it returns an empty mapping when no annotations are provided."""

        user = PlainUser(id=1, name="John Doe")

        assert not user.get_annotated_fields()

    def test_matches_annotations_with_union_types(self) -> None:
        """Test that it matches annotations nested inside union type hints."""

        user = PlainUserWithUnionAnnotation(id=1, name="John Doe")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": build_field_info(1, PrimaryKey, PrimaryKeyAnnotation)
        }

    def test_matches_annotations_with_direct_annotated_types(self) -> None:
        """Test that it matches annotations defined directly with Annotated."""

        user = PlainUserWithAnnotatedAnnotation(id=1, name="John Doe")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": build_field_info(1, PrimaryKey, PrimaryKeyAnnotation)
        }

    def test_includes_none_values(self) -> None:
        """Test that it includes None values when the field defaults to None."""

        class _PlainOptionalPK(SuperModelMixin):
            id: PrimaryKey | None
            name: str

            def __init__(self, name: str, id: PrimaryKey | None = None) -> None:
                self.id = id
                self.name = name

        user = _PlainOptionalPK(name="A")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": build_field_info(None, PrimaryKey, PrimaryKeyAnnotation)
        }

    def test_includes_falsy_non_none_values(self) -> None:
        """Test that it includes falsy values when the field is present."""

        user = PlainUser(id=0, name="Zero")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": build_field_info(0, PrimaryKey, PrimaryKeyAnnotation)
        }

    def test_matches_metadata_annotation_classes(self) -> None:
        """Test that it matches using the metadata annotation class itself."""

        user = PlainUser(id=1, name="John Doe")

        assert user.get_annotated_fields(PrimaryKeyAnnotation) == {
            "id": build_field_info(
                1,
                PrimaryKey,
                PrimaryKeyAnnotation,
                matched_metadata=(PrimaryKeyAnnotation,),
            )
        }

    def test_returns_metadata_instances_for_class_based_lookup(self) -> None:
        """Test that it returns metadata instances when matching by metadata class."""

        theme = PlainThemeConfig(accent_color="#7dd3fc", theme_name="Aurora")

        annotated_fields = theme.get_annotated_fields(ThemeColorOptions)
        field_info = annotated_fields["accent_color"]
        matched_metadata = field_info.matched_metadata

        assert field_info == build_field_info(
            "#7dd3fc",
            ThemeColorField,
            "theme_color",
            matched_metadata[0],
            matched_metadata=matched_metadata,
        )
        assert len(matched_metadata) == 1
        assert isinstance(matched_metadata[0], ThemeColorOptions)
        assert matched_metadata[0].palette == "northern-lights"
        assert matched_metadata[0].allow_gradients is True


class TestPlainClassAnnotatedFieldValue:
    """Test that the first matching annotated field is returned on plain classes."""

    def test_returns_first_matching_field_info(self) -> None:
        """Test that it returns the first matching annotated field info."""

        user = PlainUser(id=7, name="Jane")

        assert user.get_annotated_field_value(PrimaryKey) == build_field_info(
            7,
            PrimaryKey,
            PrimaryKeyAnnotation,
        )

    def test_raises_when_no_matching_field_exists(self) -> None:
        """Test that it raises when no field is annotated with the requested annotation."""

        user = PlainUserNoAnnotations(id=1, name="X")

        with pytest.raises(ValueError):
            user.get_annotated_field_value(PrimaryKey)

    def test_returns_none_when_undefined_is_allowed(self) -> None:
        """Test that it returns None when no field exists and undefined values are allowed."""

        user = PlainUserNoAnnotations(id=1, name="X")

        assert user.get_annotated_field_value(PrimaryKey, allow_undefined=True) is None

    def test_returns_field_info_for_falsy_values(self) -> None:
        """Test that it returns field info for falsy values other than None."""

        user = PlainUser(id=0, name="Zero")

        assert user.get_annotated_field_value(PrimaryKey) == build_field_info(
            0,
            PrimaryKey,
            PrimaryKeyAnnotation,
        )


class TestPlainClassGenerics:
    """Test that generic type introspection works on plain classes."""

    def test_returns_the_concrete_generic_type(self) -> None:
        """Test that it returns the concrete generic type supplied at instantiation."""

        user_with_type = PlainUserWithType[int](id=1, name="John Doe")

        assert user_with_type.get_type() is int

    def test_returns_none_when_no_generic_type_is_present(self) -> None:
        """Test that it returns None for classes without a concrete generic parameter."""

        user = PlainUser(id=1, name="John Doe")

        assert user.get_type() is None


class TestPlainClassValidation:
    """Test that FieldNotImplemented validation runs manually on plain classes."""

    def test_raises_when_not_implemented_field_is_present(self) -> None:
        """Test that it raises when validate_not_implemented_fields is called with a set field."""

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
        """Test that it passes validation when no FieldNotImplemented annotations exist."""

        user = PlainUser(id=1, name="test")

        user.validate_not_implemented_fields()
