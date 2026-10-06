from typing import ClassVar, get_origin, get_type_hints

from pydantic import BaseModel

from pydantic_super_model.models import AnnotatedFieldInfo, BoundAnnotation, FieldDeclaration


def find_annotation_match(
    annotation_type: object, annotations: tuple[object, ...]
) -> AnnotatedFieldInfo | None:
    """Return the first matched annotation carried by a type hint."""

    return BoundAnnotation(annotation_type).find_match(annotations)


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
        annotation_match = BoundAnnotation(field_type).find_match(requested_annotations)
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
