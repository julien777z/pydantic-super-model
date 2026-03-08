from typing import Self

from pydantic import BaseModel as PydanticBaseModel
from pydantic import model_validator

from pydantic_super_model._annotation_lookup import collect_annotated_fields
from pydantic_super_model._generic_resolution import resolve_generic_type
from pydantic_super_model.annotations import AnnotatedFieldInfo, FieldNotImplemented


class SuperModel(PydanticBaseModel):
    """Extend Pydantic's BaseModel with annotation and generic helpers."""

    @model_validator(mode="after")
    def validate_not_implemented_fields(self) -> Self:
        """Reject fields marked as intentionally not implemented."""

        not_implemented_fields = self.get_annotated_fields(FieldNotImplemented)

        if not_implemented_fields:
            field_names = list(not_implemented_fields)

            raise NotImplementedError(
                f"Fields {field_names} are not implemented and should be removed."
            )

        return self

    def get_type(self) -> type | None:
        """Get the concrete generic type parameter for the model."""

        return resolve_generic_type(self, SuperModel)

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
