__all__ = ["FieldNotImplemented"]


class FieldNotImplementedMarker:
    """Mark fields that are intentionally not implemented."""


FieldNotImplemented = FieldNotImplementedMarker()


def matches_requested_annotation(candidate: object, annotations: tuple[object, ...]) -> bool:
    """Return whether a candidate matches any requested annotation."""

    for annotation in annotations:
        if candidate is annotation or candidate == annotation:
            return True

        if isinstance(annotation, type) and not isinstance(candidate, type):
            if isinstance(candidate, annotation):
                return True

    return False
