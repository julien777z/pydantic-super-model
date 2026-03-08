from typing import Annotated

import pytest

from pydantic_super_model import AnnotatedFieldInfo, FieldNotImplemented, SuperModel
from tests.models.user import (
    PrimaryKey,
    ThemeColorField,
    ThemeConfig,
    User,
    UserNoAnnotations,
    UserWithAnnotatedAnnotation,
    UserWithType,
    UserWithUnionAnnotation,
    _PrimaryKeyAnnotation,
    _ThemeColorOptions,
)


def _field_info(
    value: object,
    annotation: object,
    *metadata: object,
    matched_metadata: tuple[object, ...] = (),
) -> AnnotatedFieldInfo:
    """Build an expected annotated field info object."""

    return AnnotatedFieldInfo(
        value=value,
        annotation=annotation,
        metadata=metadata,
        matched_metadata=matched_metadata,
    )


class TestModelAnnotations:
    """Test the model's get_annotated_fields method."""

    def test_model_annotations(self):
        """Test the model's get_annotated_fields method with annotations."""

        user = User(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation)}

    def test_model_no_annotations(self):
        """Test the model's get_annotated_fields method with no annotations."""

        user = UserNoAnnotations(id=1, name="John Doe")

        assert not user.get_annotated_fields(PrimaryKey)

    def test_model_with_union_annotation(self):
        """Test the model's get_annotated_fields method with union annotation."""

        user = UserWithUnionAnnotation(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation)}

    def test_model_with_annotated_annotation(self):
        """Test the model's get_annotated_fields method with annotated annotation."""

        user = UserWithAnnotatedAnnotation(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation)}

    def test_empty_annotations_returns_empty(self):
        """Return empty dict when no annotations are provided."""

        user = User(id=1, name="John Doe")

        assert not user.get_annotated_fields()

    def test_none_value_is_skipped(self):
        """Include fields set to None when explicitly provided."""

        class _UserOptionalPk(SuperModel):
            """User with optional annotated id."""

            id: PrimaryKey | None
            name: str

        user = _UserOptionalPk(id=None, name="John Doe")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(None, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_falsy_value_is_included(self):
        """Include falsy values other than None (e.g., 0)."""

        user = User(id=0, name="Zero")

        assert user.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(0, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_match_by_meta_annotation(self):
        """Match when passing the meta annotation class rather than the alias."""

        user1 = User(id=1, name="John Doe")
        user2 = UserWithAnnotatedAnnotation(id=2, name="Jane")

        assert user1.get_annotated_fields(_PrimaryKeyAnnotation) == {
            "id": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation, matched_metadata=(_PrimaryKeyAnnotation,))
        }
        assert user2.get_annotated_fields(_PrimaryKeyAnnotation) == {
            "id": _field_info(2, PrimaryKey, _PrimaryKeyAnnotation, matched_metadata=(_PrimaryKeyAnnotation,))
        }

    def test_multiple_annotations_any_match(self):
        """Return fields matching any of multiple annotations."""

        class _OtherAnnotation:
            pass

        Other = Annotated[int, _OtherAnnotation]

        class _ModelWithTwo(SuperModel):
            """Model with two differently annotated fields."""

            a: PrimaryKey
            b: Other

        m = _ModelWithTwo(a=1, b=2)

        # Single meta annotation
        assert m.get_annotated_fields(_OtherAnnotation) == {
            "b": _field_info(2, Other, _OtherAnnotation, matched_metadata=(_OtherAnnotation,))
        }

        # Any of provided should match
        out = m.get_annotated_fields(_PrimaryKeyAnnotation, _OtherAnnotation)
        assert out == {
            "a": _field_info(1, PrimaryKey, _PrimaryKeyAnnotation, matched_metadata=(_PrimaryKeyAnnotation,)),
            "b": _field_info(2, Other, _OtherAnnotation, matched_metadata=(_OtherAnnotation,)),
        }

    def test_nested_union_and_annotated(self):
        """Handle nested Union and Annotated combinations."""

        class _ModelNested(SuperModel):
            """Model with nested union types."""

            id: (Annotated[int, _PrimaryKeyAnnotation] | str) | float
            name: str

        m1 = _ModelNested(id=123, name="A")
        m2 = _ModelNested(id="x", name="B")

        expected = _field_info(
            123,
            Annotated[int, _PrimaryKeyAnnotation],
            _PrimaryKeyAnnotation,
            matched_metadata=(_PrimaryKeyAnnotation,),
        )
        assert m1.get_annotated_fields(_PrimaryKeyAnnotation) == {"id": expected}
        assert m2.get_annotated_fields(_PrimaryKeyAnnotation) == {
            "id": expected._replace(value="x")
        }

    def test_unknown_annotation_returns_empty(self):
        """Return empty dict when no field carries the requested annotation."""

        class _NoSuchAnnotation:
            pass

        user = User(id=1, name="John Doe")

        assert not user.get_annotated_fields(_NoSuchAnnotation)

    def test_unset_none_is_omitted_but_explicit_none_is_included(self):
        """Omit unset default None, include explicit None in annotated fields."""

        class _UserWithOptionalPk(SuperModel):
            """User model with optional annotated id defaulting to None."""

            id: PrimaryKey | None = None
            name: str

        # Unset None: id omitted
        user_unset = _UserWithOptionalPk(name="A")
        assert not user_unset.get_annotated_fields(PrimaryKey)

        # Explicit None: id included with None value
        user_explicit = _UserWithOptionalPk(id=None, name="B")
        assert user_explicit.get_annotated_fields(PrimaryKey) == {
            "id": _field_info(None, PrimaryKey, _PrimaryKeyAnnotation)
        }

    def test_returns_metadata_instances_for_class_based_lookup(self):
        """Test that metadata instance lookups return the metadata object."""

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


class TestModelType:
    """Test the model's get_type method."""

    def test_model_type(self):
        """Test the model's get_type method."""

        user_with_type = UserWithType[int](id=1, name="John Doe")

        assert user_with_type.get_type() is int

        user_without_type = User(id=1, name="John Doe")

        assert not user_without_type.get_type()

    def test_get_type_caches_value(self):
        """Cache the generic type value after first resolution."""

        user_with_type = UserWithType[int](id=1, name="John Doe")

        first = user_with_type.get_type()
        second = user_with_type.get_type()

        assert first is int
        assert second is int
        assert user_with_type._generic_type_value is int  # pylint: disable=protected-access


class TestValidateNotImplementedFields:
    """Test validation of fields annotated as not implemented."""

    def test_raises_when_annotated_field_is_present(self):
        """Raise NotImplementedError when an annotated field has a value."""

        class _ModelWithNotImplemented(SuperModel):
            """Model with a not-implemented field."""

            test_field: Annotated[int, FieldNotImplemented]
            name: str

        with pytest.raises(NotImplementedError):
            _ModelWithNotImplemented(test_field=1, name="x")

    def test_does_not_raise_when_annotated_field_is_none(self):
        """Do not raise when annotated field is None (skipped)."""

        class _ModelWithOptionalNotImplemented(SuperModel):
            """Model with optional not-implemented field defaulting to None."""

            test_field: Annotated[int | None, FieldNotImplemented] = None
            name: str

        test_model = _ModelWithOptionalNotImplemented(name="x")

        assert test_model.name == "x"

    def test_raises_on_falsy_non_none_value(self):
        """Raise when annotated field is falsy but not None (e.g., 0)."""

        class _ModelWithZero(SuperModel):
            """Model with not-implemented field set to zero."""

            test_field: Annotated[int, FieldNotImplemented]
            name: str

        with pytest.raises(NotImplementedError):
            _ModelWithZero(test_field=0, name="z")


class TestGetAnnotatedFieldValue:
    """Test the model's get_annotated_field_value method."""

    def test_returns_field_info_for_annotated_field(self):
        """Return annotated field info for the first matching field."""

        user = User(id=7, name="Jane")

        assert user.get_annotated_field_value(PrimaryKey) == _field_info(
            7,
            PrimaryKey,
            _PrimaryKeyAnnotation,
        )

    def test_raises_when_no_field_found(self):
        """Raise when no field is annotated with the requested annotation."""

        user = UserNoAnnotations(id=1, name="X")

        with pytest.raises(ValueError):
            user.get_annotated_field_value(PrimaryKey)

    def test_raises_when_value_is_none_and_not_allowed(self):
        """Raise when annotated field value is None and allow_none is False."""

        class _ModelOptionalPk(SuperModel):
            """Model with optional annotated id."""

            id: PrimaryKey | None
            name: str

        m = _ModelOptionalPk(id=None, name="N")

        with pytest.raises(ValueError):
            m.get_annotated_field_value(PrimaryKey)

    def test_returns_field_info_when_none_allowed(self):
        """Return field info when allow_none is True and the value is None."""

        class _ModelOptionalPk(SuperModel):
            """Model with optional annotated id."""

            id: PrimaryKey | None
            name: str

        m = _ModelOptionalPk(id=None, name="N")

        assert m.get_annotated_field_value(PrimaryKey, allow_none=True) == _field_info(
            None,
            PrimaryKey,
            _PrimaryKeyAnnotation,
        )

    def test_returns_field_info_for_falsy_zero_value(self):
        """Return field info for falsy values other than None."""

        user = User(id=0, name="Zero")

        assert user.get_annotated_field_value(PrimaryKey) == _field_info(
            0,
            PrimaryKey,
            _PrimaryKeyAnnotation,
        )

    def test_returns_field_info_with_metadata_instance_lookup(self):
        """Return field info including matched metadata instances."""

        theme = ThemeConfig(accent_color="#7dd3fc", theme_name="Aurora")
        field_info = theme.get_annotated_field_value(_ThemeColorOptions)

        assert field_info is not None
        assert field_info.value == "#7dd3fc"
        assert field_info.annotation == ThemeColorField
        assert field_info.metadata[0] == "theme_color"
        assert len(field_info.matched_metadata) == 1
        assert isinstance(field_info.matched_metadata[0], _ThemeColorOptions)
