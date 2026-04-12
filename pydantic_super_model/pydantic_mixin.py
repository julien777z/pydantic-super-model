from typing import Self

from pydantic import BaseModel, model_validator

from pydantic_super_model.annotations import AnnotatedFieldInfo
from pydantic_super_model.mixin import SuperModelMixin


class PydanticMixin(SuperModelMixin, BaseModel):
    """SuperModelMixin with Pydantic auto-validation and unset-None filtering."""

    @model_validator(mode="after")
    def _validate_not_implemented_fields(self) -> Self:
        self.validate_not_implemented_fields()
        return self

    def get_annotated_fields(self, *annotations: object) -> dict[str, AnnotatedFieldInfo]:
        """Return matched annotated fields, omitting unset default None values."""

        result = super().get_annotated_fields(*annotations)

        return {
            name: info
            for name, info in result.items()
            if info.value is not None or name in self.model_fields_set
        }
