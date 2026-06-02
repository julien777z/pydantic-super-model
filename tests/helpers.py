from pydantic_super_model import AnnotatedFieldInfo


def build_field_info(
    value: object,
    annotation: object,
    *metadata: object,
    matched_metadata: tuple[object, ...] = (),
) -> AnnotatedFieldInfo:
    """Build an expected annotated field info object."""

    return AnnotatedFieldInfo(
        value=value,
        annotation=annotation,
        metadata=metadata,
        matched_metadata=matched_metadata,
    )
