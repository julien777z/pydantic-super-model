from types import UnionType
from typing import (
    Annotated,
    ClassVar,
    NamedTuple,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel

from pydantic_super_model.annotations import AnnotatedFieldInfo

MetadataT = TypeVar("MetadataT")


class FieldDeclaration(NamedTuple):
    """Store a field's extracted metadata and the annotation holding its nested metadata."""

    metadata: tuple[object, ...]
    annotation: object


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


def annotation_metadata(annotation: object) -> tuple[object, ...]:
    """Return every metadata item an annotation carries, outermost first."""

    origin = get_origin(annotation)

    if origin in (Union, UnionType):
        return tuple(
            metadata_item
            for union_member in get_args(annotation)
            for metadata_item in annotation_metadata(union_member)
        )

    if origin is Annotated:
        inner_type, *metadata = get_args(annotation)

        return (*metadata, *annotation_metadata(inner_type))

    return ()


def field_declarations(model_type: type[object]) -> dict[str, FieldDeclaration]:
    """Return each declared field's extracted metadata and annotation, in declaration order."""

    if issubclass(model_type, BaseModel):
        return {
            field_name: FieldDeclaration(tuple(field_info.metadata), field_info.annotation)
            for field_name, field_info in model_type.model_fields.items()
        }

    return {
        field_name: FieldDeclaration((), annotation)
        for field_name, annotation in get_type_hints(model_type, include_extras=True).items()
        if get_origin(annotation) is not ClassVar
    }


def matching_metadata(
    declaration: FieldDeclaration,
    metadata_types: tuple[type[MetadataT], ...],
) -> tuple[MetadataT, ...]:
    """Return a declaration's metadata instances of the requested types, outermost first."""

    return tuple(
        metadata_item
        for metadata_item in (*declaration.metadata, *annotation_metadata(declaration.annotation))
        if isinstance(metadata_item, metadata_types)
    )


def collect_annotated_declarations(
    model: object,
    *annotations: object,
) -> dict[str, AnnotatedFieldInfo]:
    """Collect annotated declarations, including any a model does not expose as a field."""

    if not annotations:
        return {}

    is_class = isinstance(model, type)
    model_type = model if is_class else type(model)
    requested_annotations = tuple(annotations)
    result: dict[str, AnnotatedFieldInfo] = {}

    for field_name, field_type in get_type_hints(model_type, include_extras=True).items():
        annotation_match = find_annotation_match(field_type, requested_annotations)
        if annotation_match is None:
            continue

        value = None if is_class else getattr(model, field_name, None)
        result[field_name] = annotation_match._replace(value=value)

    return result


def collect_annotated_fields(model: object, *annotations: object) -> dict[str, AnnotatedFieldInfo]:
    """Collect fields whose type hints carry any requested annotation."""

    declarations = collect_annotated_declarations(model, *annotations)
    model_type = model if isinstance(model, type) else type(model)

    if not issubclass(model_type, BaseModel):
        return declarations

    field_names = frozenset(model_type.model_fields)

    return {
        field_name: annotated_field
        for field_name, annotated_field in declarations.items()
        if field_name in field_names
    }
