from types import UnionType
from typing import Any, Annotated, Union, get_args, get_origin, get_type_hints
from typing_extensions import Self
from pydantic import BaseModel as PydanticBaseModel, model_validator
from generics import get_filled_type

__all__ = ["SuperModel", "FieldNotImplemented"]


class _FieldNotImplemented:  # pylint: disable=too-few-public-methods
    """
    Annotation for fields that are not implemented.
    If a field is annotated with this and it is presented in the model,
    this library will raise a NotImplementedError.
    """


FieldNotImplemented = _FieldNotImplemented()


class SuperModel(PydanticBaseModel):
    """Pydantic BaseModel with extra methods."""

    _generic_type_value: Any = None

    @model_validator(mode="after")
    def validate_not_implemented_fields(self) -> Self:
        """Validate that all fields are implemented."""

        not_implemented_fields = self.get_annotated_fields(FieldNotImplemented)

        if not_implemented_fields:
            raise NotImplementedError(
                f"Fields {not_implemented_fields} are not implemented and should be removed."
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

    def get_annotated_fields(self, *annotations: type) -> dict[str, Any]:
        """Return fields whose type hints carry any of the given annotations."""

        if not annotations:
            return {}

        def matches_requested_annotation(candidate: object) -> bool:
            """Return True if candidate equals or is any requested annotation."""

            return any(candidate is ann or candidate == ann for ann in annotations)

        def _has_requested_annotation(tp: object) -> bool:
            """Return True if tp (directly or via wrappers) carries a requested annotation."""

            if matches_requested_annotation(tp):
                return True

            origin = get_origin(tp)

            if origin in (Union, UnionType):
                return any(_has_requested_annotation(arg) for arg in get_args(tp))

            if origin is Annotated:
                _, *meta = get_args(tp)

                return any(matches_requested_annotation(m) for m in meta)

            return False

        type_hints = get_type_hints(type(self), include_extras=True)
        result: dict[str, Any] = {}

        for field_name, field_type in type_hints.items():
            if _has_requested_annotation(field_type):
                value = getattr(self, field_name, None)

                # Include fields explicitly set (even if value is None),
                # or any non-None values.
                if field_name in self.model_fields_set or value is not None:
                    result[field_name] = value

        return result
