from typing import Any, NamedTuple

__all__ = ["AnnotatedFieldInfo", "FieldNotImplemented"]


class _FieldNotImplemented:
    """Mark fields that are intentionally not implemented."""


FieldNotImplemented = _FieldNotImplemented()


class AnnotatedFieldInfo(NamedTuple):
    """Store a matched annotated field value and its metadata."""

    value: Any
    annotation: object
    metadata: tuple[object, ...]
    matched_metadata: tuple[object, ...]
