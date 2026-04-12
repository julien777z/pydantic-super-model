from types import UnionType
from typing import Annotated, Any, Union, get_args, get_origin, get_type_hints

from pydantic_super_model.annotations import AnnotatedFieldInfo


def _matches_requested_annotation(candidate: object, annotations: tuple[object, ...]) -> bool:
    """Return whether a candidate matches any requested annotation."""

    for annotation in annotations:
        if candidate is annotation or candidate == annotation:
            return True

        if isinstance(annotation, type) and not isinstance(candidate, type):
            if isinstance(candidate, annotation):
                return True

    return False


def _find_annotation_match(
    annotation_type: object,
    annotations: tuple[object, ...],
) -> AnnotatedFieldInfo | None:
    """Return the first matched annotation carried by a type hint."""

    origin = get_origin(annotation_type)

    if origin in (Union, UnionType):
        for union_member in get_args(annotation_type):
            match = _find_annotation_match(union_member, annotations)
            if match is not None:
                return match

        return None

    if origin is Annotated:
        inner_type, *metadata = get_args(annotation_type)
        matched_metadata = tuple(
            metadata_item
            for metadata_item in metadata
            if _matches_requested_annotation(metadata_item, annotations)
        )

        if matched_metadata or _matches_requested_annotation(annotation_type, annotations):
            return AnnotatedFieldInfo(
                value=None,
                annotation=annotation_type,
                metadata=tuple(metadata),
                matched_metadata=matched_metadata,
            )

        return _find_annotation_match(inner_type, annotations)

    if _matches_requested_annotation(annotation_type, annotations):
        return AnnotatedFieldInfo(
            value=None,
            annotation=annotation_type,
            metadata=(),
            matched_metadata=(),
        )

    return None


def collect_annotated_fields(
    model: object,
    *annotations: object,
) -> dict[str, AnnotatedFieldInfo]:
    """Collect fields whose type hints carry any requested annotation."""

    if not annotations:
        return {}

    type_hints = get_type_hints(type(model), include_extras=True)
    result: dict[str, AnnotatedFieldInfo] = {}
    requested_annotations = tuple(annotations)

    for field_name, field_type in type_hints.items():
        annotation_match = _find_annotation_match(field_type, requested_annotations)
        if annotation_match is None:
            continue

        value = getattr(model, field_name, None)
        result[field_name] = annotation_match._replace(value=value)

    return result
