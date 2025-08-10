from typing import Annotated, Generic, TypeVar
from super_model import BaseModel


class _PrimaryKeyAnnotation:
    pass


PrimaryKey = Annotated[int, _PrimaryKeyAnnotation]
GenericType = TypeVar("GenericType", bound=int)


class User(BaseModel):
    """User test model."""

    id: PrimaryKey
    name: str


class UserNoAnnotations(BaseModel):
    """User test model without annotations."""

    id: int
    name: str


class UserWithUnionAnnotation(BaseModel):
    """User test model with union."""

    id: PrimaryKey | str
    name: str


class UserWithAnnotatedAnnotation(BaseModel):
    """User test model with annotated annotation."""

    id: Annotated[int, _PrimaryKeyAnnotation]
    name: str


class UserWithType(BaseModel, Generic[GenericType]):
    """User test model with type."""

    id: GenericType
    name: str
