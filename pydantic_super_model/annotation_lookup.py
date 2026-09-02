from types import UnionType
from typing import Annotated, TypeVar, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from pydantic_super_model.annotations import AnnotatedFieldInfo

MetadataT = TypeVar("MetadataT")


def matches_requested_annotation(candidate: object, annotations: tuple[object, ...]) -> bool:
    """Return whether a candidate matches any requested annotation."""

    for annotation in annotations:
        if candidate is annotation or candidate == annotation:
            return True

        if isinstance(annotation, type) and not isinstance(candidate, type):
            if isinstance(candidate, annotation):
                return True

    return False


def find_annotation_match(
    annotation_type: object,
    annotations: tuple[object, ...],
) -> AnnotatedFieldInfo | None:
    """Return the first matched annotation carried by a type hint."""

    origin = get_origin(annotation_type)

    if origin in (Union, UnionType):
        for union_member in get_args(annotation_type):
            match = find_annotation_match(union_member, annotations)
            if match is not None:
                return match

        return None

    if origin is Annotated:
        inner_type, *metadata = get_args(annotation_type)
        matched_metadata = tuple(
            metadata_item
            for metadata_item in metadata
            if matches_requested_annotation(metadata_item, annotations)
        )

        if matched_metadata or matches_requested_annotation(annotation_type, annotations):
            return AnnotatedFieldInfo(
                value=None,
                annotation=annotation_type,
                metadata=tuple(metadata),
                matched_metadata=matched_metadata,
            )

        return find_annotation_match(inner_type, annotations)

    if matches_requested_annotation(annotation_type, annotations):
        return AnnotatedFieldInfo(
            value=None,
            annotation=annotation_type,
            metadata=(),
            matched_metadata=(),
        )

    return None


def field_metadata_sources(model_type: type[object], field_name: str) -> tuple[tuple[object, ...], object]:
    """Return a field's extracted metadata and the annotation still holding nested metadata."""

    if issubclass(model_type, BaseModel):
        if field_name in model_type.model_fields:
            field_info = model_type.model_fields[field_name]

            return tuple(field_info.metadata), field_info.annotation
    else:
        type_hints = get_type_hints(model_type, include_extras=True)

        if field_name in type_hints:
            return (), type_hints[field_name]

    raise KeyError(f"{model_type.__name__} has no field '{field_name}'.")


def declared_field_names(model_type: type[object]) -> tuple[str, ...]:
    """Return a class's declared field names in declaration order."""

    if issubclass(model_type, BaseModel):
        return tuple(model_type.model_fields)

    return tuple(get_type_hints(model_type, include_extras=True))


def collect_field_metadata(
    model_type: type[object],
    field_name: str,
    *metadata_types: type[MetadataT],
) -> tuple[MetadataT, ...]:
    """Collect a field's metadata instances of the requested types, in declaration order."""

    if not metadata_types:
        return ()

    extracted_metadata, nested_annotation = field_metadata_sources(model_type, field_name)
    nested_match = find_annotation_match(nested_annotation, metadata_types)
    nested_metadata = nested_match.matched_metadata if nested_match is not None else ()

    return tuple(
        metadata_item
        for metadata_item in (*extracted_metadata, *nested_metadata)
        if isinstance(metadata_item, metadata_types)
    )


def collect_annotated_fields(
    model: object | type[object],
    *annotations: object,
) -> dict[str, AnnotatedFieldInfo]:
    """Collect fields whose type hints carry any requested annotation."""

    if not annotations:
        return {}

    is_class = isinstance(model, type)
    model_type = model if is_class else type(model)
    type_hints = get_type_hints(model_type, include_extras=True)
    result: dict[str, AnnotatedFieldInfo] = {}
    requested_annotations = tuple(annotations)

    for field_name, field_type in type_hints.items():
        annotation_match = find_annotation_match(field_type, requested_annotations)
        if annotation_match is None:
            continue

        value = None if is_class else getattr(model, field_name, None)
        result[field_name] = annotation_match._replace(value=value)

    return result
