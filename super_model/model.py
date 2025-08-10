from typing import Any, Optional, get_origin, get_args, get_type_hints, Annotated, Union
from pydantic import BaseModel as PydanticBaseModel
from generics import get_filled_type

__all__ = ["SuperModel"]


class SuperModel(PydanticBaseModel):
    """Pydantic BaseModel with extra methods."""

    _generic_type_value: Any = None

    def get_type(self) -> Optional[type]:
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

        def has_requested_annotation(tp: object) -> bool:
            """Return True if tp directly or indirectly includes any annotation in annotations."""

            # Direct match with the provided annotation(s)
            if any(tp is ann or tp == ann for ann in annotations):
                return True

            origin = get_origin(tp)

            # Union: check any branch
            if origin is Union:
                return any(has_requested_annotation(arg) for arg in get_args(tp))

            # Annotated: check extras after the underlying type
            if origin is Annotated:
                meta = get_args(tp)[1:]
                return any(any(m is ann or m == ann for ann in annotations) for m in meta)

            return False

        type_hints = get_type_hints(type(self), include_extras=True)
        result: dict[str, Any] = {}

        for field_name, field_type in type_hints.items():
            if has_requested_annotation(field_type):
                value = getattr(self, field_name, None)
                if value is not None:
                    result[field_name] = value

        return result
