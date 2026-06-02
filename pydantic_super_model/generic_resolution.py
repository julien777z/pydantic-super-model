from typing import Final

from generics import get_filled_type

GENERIC_TYPE_CACHE_ATTR: Final[str] = "_pydantic_super_model_cached_generic_type"
UNRESOLVED_GENERIC_TYPE: Final[object] = object()


def resolve_generic_type(model: object, super_model_type: type[object]) -> type | None:
    """Resolve and cache the model's concrete generic type parameter."""

    cached_type = getattr(model, GENERIC_TYPE_CACHE_ATTR, UNRESOLVED_GENERIC_TYPE)

    if cached_type is not UNRESOLVED_GENERIC_TYPE:
        return cached_type

    try:
        resolved_type = get_filled_type(model, super_model_type, 0)
    except TypeError:
        resolved_type = None

    setattr(model, GENERIC_TYPE_CACHE_ATTR, resolved_type)

    return resolved_type
