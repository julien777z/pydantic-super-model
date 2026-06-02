from typing import Any, NamedTuple

__all__ = ["AnnotatedFieldInfo", "FieldNotImplemented"]


class FieldNotImplementedMarker:
    """Mark fields that are intentionally not implemented."""


FieldNotImplemented = FieldNotImplementedMarker()


class AnnotatedFieldInfo(NamedTuple):
    """Store a matched annotated field value and its metadata."""

    value: Any
    annotation: object
    metadata: tuple[object, ...]
    matched_metadata: tuple[object, ...]
