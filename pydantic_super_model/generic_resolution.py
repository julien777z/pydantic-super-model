from enum import Enum, auto
from typing import Final, Literal

from generics import get_filled_type

GENERIC_TYPE_CACHE_ATTR: Final[str] = "_pydantic_super_model_cached_generic_type"


class GenericTypeCache(Enum):
    """Mark a model whose generic type parameter has not been resolved yet."""

    UNRESOLVED = auto()


def resolve_generic_type(model: object, super_model_type: type[object]) -> type | None:
    """Resolve and cache the model's concrete generic type parameter."""

    cached_type: type | None | Literal[GenericTypeCache.UNRESOLVED] = getattr(
        model, GENERIC_TYPE_CACHE_ATTR, GenericTypeCache.UNRESOLVED
    )

    if cached_type is not GenericTypeCache.UNRESOLVED:
        return cached_type

    try:
        resolved_type: type | None = get_filled_type(model, super_model_type, 0)
    except TypeError:
        resolved_type = None

    setattr(model, GENERIC_TYPE_CACHE_ATTR, resolved_type)

    return resolved_type
