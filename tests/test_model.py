from typing import Annotated
import pytest
from super_model import SuperModel, FieldNotImplemented
from tests.models.user import (
    User,
    PrimaryKey,
    UserNoAnnotations,
    UserWithUnionAnnotation,
    UserWithAnnotatedAnnotation,
    UserWithType,
    _PrimaryKeyAnnotation,
)


class TestModelAnnotations:
    """Test the model's get_annotated_fields method."""

    def test_model_annotations(self):
        """Test the model's get_annotated_fields method with annotations."""

        user = User(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": 1}

    def test_model_no_annotations(self):
        """Test the model's get_annotated_fields method with no annotations."""

        user = UserNoAnnotations(id=1, name="John Doe")

        assert not user.get_annotated_fields(PrimaryKey)

    def test_model_with_union_annotation(self):
        """Test the model's get_annotated_fields method with union annotation."""

        user = UserWithUnionAnnotation(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": 1}

    def test_model_with_annotated_annotation(self):
        """Test the model's get_annotated_fields method with annotated annotation."""

        user = UserWithAnnotatedAnnotation(id=1, name="John Doe")

        annotated_fields = user.get_annotated_fields(PrimaryKey)

        assert annotated_fields == {"id": 1}

    def test_empty_annotations_returns_empty(self):
        """Return empty dict when no annotations are provided."""

        user = User(id=1, name="John Doe")

        assert not user.get_annotated_fields()

    def test_none_value_is_skipped(self):
        """Skip fields with None value even if annotated."""

        class _UserOptionalPk(SuperModel):
            """User with optional annotated id."""

            id: PrimaryKey | None
            name: str

        user = _UserOptionalPk(id=None, name="John Doe")

        assert not user.get_annotated_fields(PrimaryKey)

    def test_falsy_value_is_included(self):
        """Include falsy values other than None (e.g., 0)."""

        user = User(id=0, name="Zero")

        assert user.get_annotated_fields(PrimaryKey) == {"id": 0}

    def test_match_by_meta_annotation(self):
        """Match when passing the meta annotation class rather than the alias."""

        user1 = User(id=1, name="John Doe")
        user2 = UserWithAnnotatedAnnotation(id=2, name="Jane")

        assert user1.get_annotated_fields(_PrimaryKeyAnnotation) == {"id": 1}
        assert user2.get_annotated_fields(_PrimaryKeyAnnotation) == {"id": 2}

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
        assert m.get_annotated_fields(_OtherAnnotation) == {"b": 2}

        # Any of provided should match
        out = m.get_annotated_fields(_PrimaryKeyAnnotation, _OtherAnnotation)
        assert out == {"a": 1, "b": 2}

    def test_nested_union_and_annotated(self):
        """Handle nested Union and Annotated combinations."""

        class _ModelNested(SuperModel):
            """Model with nested union types."""

            id: (Annotated[int, _PrimaryKeyAnnotation] | str) | float
            name: str

        m1 = _ModelNested(id=123, name="A")
        m2 = _ModelNested(id="x", name="B")

        assert m1.get_annotated_fields(_PrimaryKeyAnnotation) == {"id": 123}
        assert m2.get_annotated_fields(_PrimaryKeyAnnotation) == {"id": "x"}

    def test_unknown_annotation_returns_empty(self):
        """Return empty dict when no field carries the requested annotation."""

        class _NoSuchAnnotation:
            pass

        user = User(id=1, name="John Doe")

        assert not user.get_annotated_fields(_NoSuchAnnotation)


class TestModelType:
    """Test the model's get_type method."""

    def test_model_type(self):
        """Test the model's get_type method."""

        user_with_type = UserWithType[int](id=1, name="John Doe")

        assert user_with_type.get_type() == int

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
