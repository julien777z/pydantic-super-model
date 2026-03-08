from types import UnionType
from typing import Annotated, Any, NamedTuple, Self, Union, get_args, get_origin, get_type_hints

from generics import get_filled_type
from pydantic import BaseModel as PydanticBaseModel
from pydantic import model_validator

__all__ = ["SuperModel", "FieldNotImplemented", "AnnotatedFieldInfo"]


class _FieldNotImplemented:  # pylint: disable=too-few-public-methods
    """
    Annotation for fields that are not implemented.
    If a field is annotated with this and it is presented in the model,
    this library will raise a NotImplementedError.
    """


FieldNotImplemented = _FieldNotImplemented()


class AnnotatedFieldInfo(NamedTuple):
    """Store a matched annotated field value and its metadata."""

    value: Any
    annotation: object
    metadata: tuple[object, ...]
    matched_metadata: tuple[object, ...]


class SuperModel(PydanticBaseModel):
    """Pydantic BaseModel with extra methods."""

    _generic_type_value: Any = None

    @model_validator(mode="after")
    def validate_not_implemented_fields(self) -> Self:
        """Validate that all fields are implemented."""

        not_implemented_fields = self.get_annotated_fields(FieldNotImplemented)

        if not_implemented_fields:
            field_names = list(not_implemented_fields)

            raise NotImplementedError(
                f"Fields {field_names} are not implemented and should be removed."
            )

        return self

    def get_type(self) -> type | None:
        """Get the type of the model."""

        if self._generic_type_value:
            return self._generic_type_value

        try:
            self._generic_type_value = get_filled_type(self, SuperModel, 0)
        except TypeError:
            return None

        return self._generic_type_value

    def get_annotated_fields(self, *annotations: object) -> dict[str, AnnotatedFieldInfo]:
        """Return matched annotated fields with values and annotation metadata."""

        if not annotations:
            return {}

        def matches_requested_annotation(candidate: object) -> bool:
            """Return True if candidate matches any requested annotation or metadata type."""

            for annotation in annotations:
                if candidate is annotation or candidate == annotation:
                    return True

                if isinstance(annotation, type) and not isinstance(candidate, type):
                    if isinstance(candidate, annotation):
                        return True

            return False

        def _find_annotation_match(tp: object) -> AnnotatedFieldInfo | None:
            """Return metadata for the first matching annotation carried by tp."""
            origin = get_origin(tp)

            if origin in (Union, UnionType):
                for arg in get_args(tp):
                    match = _find_annotation_match(arg)
                    if match is not None:
                        return match

                return None

            if origin is Annotated:
                _, *metadata = get_args(tp)
                matched_metadata = tuple(meta for meta in metadata if matches_requested_annotation(meta))

                if matched_metadata or matches_requested_annotation(tp):
                    return AnnotatedFieldInfo(
                        value=None,
                        annotation=tp,
                        metadata=tuple(metadata),
                        matched_metadata=matched_metadata,
                    )

                return _find_annotation_match(get_args(tp)[0])

            if matches_requested_annotation(tp):
                return AnnotatedFieldInfo(
                    value=None,
                    annotation=tp,
                    metadata=(),
                    matched_metadata=(),
                )

            return None

        type_hints = get_type_hints(type(self), include_extras=True)
        result: dict[str, AnnotatedFieldInfo] = {}

        for field_name, field_type in type_hints.items():
            annotation_match = _find_annotation_match(field_type)
            if annotation_match is not None:
                value = getattr(self, field_name, None)

                # Include fields explicitly set (even if value is None),
                # or any non-None values.
                if field_name in self.model_fields_set or value is not None:
                    result[field_name] = annotation_match._replace(value=value)

        return result

    def get_annotated_field_value(
        self, annotation: object, allow_none: bool = False, allow_undefined: bool = False
    ) -> AnnotatedFieldInfo | None:
        """Return the first matched annotated field with its value and metadata."""

        annotated_fields = self.get_annotated_fields(annotation)

        if not annotated_fields:
            if allow_undefined:
                return None

            raise ValueError(f"No field annotated with {annotation} found.")

        field_name, annotated_field = next(iter(annotated_fields.items()))
        annotated_field_value = annotated_field.value

        if not allow_none and annotated_field_value is None:
            raise ValueError(f"Field '{field_name}' is None; pass allow_none=True to accept None.")

        return annotated_field
