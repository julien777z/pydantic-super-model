from typing import TypeVar

from pydantic_super_model.annotation_lookup import (
    collect_annotated_fields,
    collect_field_metadata,
    collect_field_names_with_metadata,
)
from pydantic_super_model.annotations import AnnotatedFieldInfo, FieldNotImplemented
from pydantic_super_model.generic_resolution import resolve_generic_type

MetadataT = TypeVar("MetadataT")


class SuperModelMixin:
    """Mixin for annotation introspection and generic type resolution."""

    def validate_not_implemented_fields(self) -> None:
        """Reject fields marked as intentionally not implemented."""

        not_implemented_fields = self.get_annotated_fields(FieldNotImplemented)

        if not_implemented_fields:
            field_names = list(not_implemented_fields)

            raise NotImplementedError(f"Fields {field_names} are not implemented and should be removed.")

    def get_type(self) -> type | None:
        """Get the concrete generic type parameter for the instance."""

        return resolve_generic_type(self, SuperModelMixin)

    def get_annotated_fields(self, *annotations: object) -> dict[str, AnnotatedFieldInfo]:
        """Return matched annotated fields with values and annotation metadata."""

        return collect_annotated_fields(self, *annotations)

    def get_annotated_field_value(
        self,
        annotation: object,
        allow_none: bool = False,
        allow_undefined: bool = False,
    ) -> AnnotatedFieldInfo | None:
        """Return the first matched annotated field with its value and metadata."""

        annotated_fields = self.get_annotated_fields(annotation)

        if not annotated_fields:
            if allow_undefined:
                return None

            raise ValueError(f"No field annotated with {annotation} found.")

        field_name, annotated_field = next(iter(annotated_fields.items()))

        if not allow_none and annotated_field.value is None:
            raise ValueError(f"Field '{field_name}' is None; pass allow_none=True to accept None.")

        return annotated_field

    @classmethod
    def field_metadata(cls, field_name: str, *metadata_types: type[MetadataT]) -> tuple[MetadataT, ...]:
        """Return a field's metadata instances of the requested types, in declaration order."""

        return collect_field_metadata(cls, field_name, *metadata_types)

    @classmethod
    def first_field_metadata(cls, field_name: str, metadata_type: type[MetadataT]) -> MetadataT | None:
        """Return a field's first metadata instance of the requested type, or None."""

        return next(iter(cls.field_metadata(field_name, metadata_type)), None)

    @classmethod
    def field_names_with_metadata(cls, *metadata_types: type[object]) -> frozenset[str]:
        """Return the names of fields carrying metadata of any requested type."""

        return collect_field_names_with_metadata(cls, *metadata_types)
