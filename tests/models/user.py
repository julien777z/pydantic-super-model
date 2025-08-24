from typing import Annotated, Generic, TypeVar

from super_model import SuperModel


class _PrimaryKeyAnnotation:
    pass


PrimaryKey = Annotated[int, _PrimaryKeyAnnotation]
GenericType = TypeVar("GenericType", bound=int)


class User(SuperModel):
    """User test model."""

    id: PrimaryKey
    name: str


class UserNoAnnotations(SuperModel):
    """User test model without annotations."""

    id: int
    name: str


class UserWithUnionAnnotation(SuperModel):
    """User test model with union."""

    id: PrimaryKey | str
    name: str


class UserWithAnnotatedAnnotation(SuperModel):
    """User test model with annotated annotation."""

    id: Annotated[int, _PrimaryKeyAnnotation]
    name: str


class UserWithType(SuperModel, Generic[GenericType]):
    """User test model with type."""

    id: GenericType
    name: str
