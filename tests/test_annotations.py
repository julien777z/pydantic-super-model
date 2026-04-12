from typing import Annotated

import pytest
from pydantic import BaseModel

from pydantic_super_model import SuperModelMixin
from tests.helpers import _field_info
from tests.models.user import (
    PrimaryKey,
    ThemeColorField,
    ThemeConfig,
    User,
    UserNoAnnotations,
    UserWithAnnotatedAnnotation,
    UserWithUnionAnnotation,
    _PrimaryKeyAnnotation,
    _ThemeColorOptions,
)


class TestAnnotatedFields:
    """Test annotated field discovery behavior."""

    def test_returns_matching_annotated_fields(self) -> None:
        """Return fields that carry the requested annotation."""

        user = User(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation)}

    def test_returns_empty_when_model_has_no_annotations(self) -> None:
        """Return an empty mapping when no matching annotations exist."""

        user = UserNoAnnotations(id=1, name="John Doe")

        assert not user.get_annotated_fields(PrimaryKey)

    def test_returns_empty_when_no_annotations_are_requested(self) -> None:
        """Return an empty mapping when no annotations are provided."""

        user = User(id=1, name="John Doe")

        assert not user.get_annotated_fields()

    def test_matches_annotations_with_union_types(self) -> None:
        """Match annotations nested inside union type hints."""

        user = UserWithUnionAnnotation(id=1, name="John Doe")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_matches_annotations_with_direct_annotated_types(self) -> None:
        """Match annotations defined directly with Annotated."""

        user = UserWithAnnotatedAnnotation(id=1, name="John Doe")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_includes_explicit_none_values(self) -> None:
        """Include annotated fields explicitly provided as None."""

        class _UserOptionalPrimaryKey(SuperModelMixin, BaseModel):
            """Model with an optional annotated primary key."""

            id: PrimaryKey | None
            name: str

        user = _UserOptionalPrimaryKey(id=None, name="John Doe")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(None, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_includes_falsy_non_none_values(self) -> None:
        """Include falsy values when the field is present."""

        user = User(id=0, name="Zero")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(0, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_matches_metadata_annotation_classes(self) -> None:
        """Match using the metadata annotation class itself."""

        user = User(id=1, name="John Doe")
        annotated_user = UserWithAnnotatedAnnotation(id=2, name="Jane")

        assert user.get_annotated_fields(_PrimaryKeyAnnotation) == {
            "id": _field_info(
                1,
                PrimaryKey,
                _PrimaryKeyAnnotation,
                matched_metadata=(_PrimaryKeyAnnotation,),
            )
        }
        assert annotated_user.get_annotated_fields(_PrimaryKeyAnnotation) == {
            "id": _field_info(
                2,
                PrimaryKey,
                _PrimaryKeyAnnotation,
                matched_metadata=(_PrimaryKeyAnnotation,),
            )
        }

    def test_matches_any_requested_annotation(self) -> None:
        """Return fields matching any provided annotation."""

        class _OtherAnnotation:
            """Metadata marker for another annotated field."""

        other_annotation = Annotated[int, _OtherAnnotation]

        class _ModelWithTwoAnnotatedFields(SuperModelMixin, BaseModel):
            """Model with two different annotated fields."""

            first: PrimaryKey
            second: other_annotation

        model = _ModelWithTwoAnnotatedFields(first=1, second=2)

        assert model.get_annotated_fields(_OtherAnnotation) == {
            "second": _field_info(
                2,
                other_annotation,
                _OtherAnnotation,
                matched_metadata=(_OtherAnnotation,),
            )
        }

        assert model.get_annotated_fields(_PrimaryKeyAnnotation, _OtherAnnotation) == {
            "first": _field_info(
                1,
                PrimaryKey,
                _PrimaryKeyAnnotation,
                matched_metadata=(_PrimaryKeyAnnotation,),
            ),
            "second": _field_info(
                2,
                other_annotation,
                _OtherAnnotation,
                matched_metadata=(_OtherAnnotation,),
            ),
        }

    def test_handles_nested_unions_and_annotated_types(self) -> None:
        """Return the first matching annotation found in nested unions."""

        class _NestedModel(SuperModelMixin, BaseModel):
            """Model with nested unions carrying annotated members."""

            id: (Annotated[int, _PrimaryKeyAnnotation] | str) | float
            name: str

        int_model = _NestedModel(id=123, name="A")
        str_model = _NestedModel(id="x", name="B")

        expected = _field_info(
            123,
            Annotated[int, _PrimaryKeyAnnotation],
            _PrimaryKeyAnnotation,
            matched_metadata=(_PrimaryKeyAnnotation,),
        )

        assert int_model.get_annotated_fields(_PrimaryKeyAnnotation) == {"id": expected}
        assert str_model.get_annotated_fields(_PrimaryKeyAnnotation) == {
            "id": expected._replace(value="x")
        }

    def test_returns_empty_for_unknown_annotations(self) -> None:
        """Return an empty mapping when no field carries the annotation."""

        class _MissingAnnotation:
            """Unknown annotation marker used only in this test."""

        user = User(id=1, name="John Doe")

        assert not user.get_annotated_fields(_MissingAnnotation)

    def test_returns_metadata_instances_for_class_based_lookup(self) -> None:
        """Return metadata instances when matching by metadata class."""

        theme = ThemeConfig(accent_color="#7dd3fc", theme_name="Aurora")

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

    def test_includes_inherited_annotated_fields(self) -> None:
        """Return annotated fields inherited from a parent model."""

        class _InheritedUser(User):
            """Extend the base user model with another field."""

            email: str

        user = _InheritedUser(id=5, name="Taylor", email="taylor@example.com")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(5, PrimaryKey, _PrimaryKeyAnnotation)
        }


class TestAnnotatedFieldValue:
    """Test access to the first matching annotated field."""

    def test_returns_first_matching_field_info(self) -> None:
        """Return the first matching annotated field info."""

        user = User(id=7, name="Jane")

        assert user.get_annotated_field_value(PrimaryKey) == _field_info(
            7,
            PrimaryKey,
            _PrimaryKeyAnnotation,
        )

    def test_raises_when_no_matching_field_exists(self) -> None:
        """Raise when no field is annotated with the requested annotation."""

        user = UserNoAnnotations(id=1, name="X")

        with pytest.raises(ValueError):
            user.get_annotated_field_value(PrimaryKey)

    def test_returns_none_when_undefined_is_allowed(self) -> None:
        """Return None when no field exists and undefined values are allowed."""

        user = UserNoAnnotations(id=1, name="X")

        assert user.get_annotated_field_value(PrimaryKey, allow_undefined=True) is None

    def test_raises_when_value_is_none_and_none_is_not_allowed(self) -> None:
        """Raise when the matched field value is None."""

        class _OptionalPrimaryKeyModel(SuperModelMixin, BaseModel):
            """Model with an optional annotated primary key."""

            id: PrimaryKey | None
            name: str

        model = _OptionalPrimaryKeyModel(id=None, name="N")

        with pytest.raises(ValueError):
            model.get_annotated_field_value(PrimaryKey)

    def test_returns_field_info_when_none_is_allowed(self) -> None:
        """Return field info when allow_none is enabled."""

        class _OptionalPrimaryKeyModel(SuperModelMixin, BaseModel):
            """Model with an optional annotated primary key."""

            id: PrimaryKey | None
            name: str

        model = _OptionalPrimaryKeyModel(id=None, name="N")

        assert model.get_annotated_field_value(PrimaryKey, allow_none=True) == _field_info(
            None,
            PrimaryKey,
            _PrimaryKeyAnnotation,
        )

    def test_returns_field_info_for_falsy_values(self) -> None:
        """Return field info for falsy values other than None."""

        user = User(id=0, name="Zero")

        assert user.get_annotated_field_value(PrimaryKey) == _field_info(
            0,
            PrimaryKey,
            _PrimaryKeyAnnotation,
        )

    def test_returns_field_info_with_metadata_instances(self) -> None:
        """Return matched metadata instances for class-based lookup."""

        theme = ThemeConfig(accent_color="#7dd3fc", theme_name="Aurora")
        field_info = theme.get_annotated_field_value(_ThemeColorOptions)

        assert field_info is not None
        assert field_info.value == "#7dd3fc"
        assert field_info.annotation == ThemeColorField
        assert field_info.metadata[0] == "theme_color"
        assert len(field_info.matched_metadata) == 1
        assert isinstance(field_info.matched_metadata[0], _ThemeColorOptions)

    def test_returns_the_first_match_in_field_definition_order(self) -> None:
        """Return the first matching field based on model field order."""

        class _TwoPrimaryKeys(SuperModelMixin, BaseModel):
            """Model with two fields carrying the same annotation."""

            first_id: PrimaryKey
            second_id: PrimaryKey

        model = _TwoPrimaryKeys(first_id=1, second_id=2)

        assert model.get_annotated_field_value(PrimaryKey) == _field_info(
            1,
            PrimaryKey,
            _PrimaryKeyAnnotation,
        )
