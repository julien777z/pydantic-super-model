from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType, UnionType
from typing import Annotated, Any, NamedTuple, TypeVar, Union, get_args, get_origin

from typing_inspection.typing_objects import is_typealiastype

from pydantic_super_model.annotations import matches_requested_annotation

MetadataT = TypeVar("MetadataT")


class AnnotatedFieldInfo(NamedTuple):
    """Store a matched annotated field value and its metadata."""

    value: Any
    annotation: object
    metadata: tuple[object, ...]
    matched_metadata: tuple[object, ...]


class BoundAnnotation(NamedTuple):
    """Store an annotation with the lexical bindings that supplied it."""

    annotation: object
    bindings: Mapping[TypeVar, BoundAnnotation] = MappingProxyType({})
    expansion_trail: frozenset[int] = frozenset()

    def resolve(self) -> BoundAnnotation:
        """Resolve a parameter through the incoming environments captured by aliases."""

        bound = self

        while isinstance(bound.annotation, TypeVar) and bound.annotation in bound.bindings:
            bound = bound.bindings[bound.annotation]

        return bound

    def alias_bindings(
        self, parameters: tuple[object, ...], arguments: tuple[object, ...], expansion_trail: frozenset[int]
    ) -> Mapping[TypeVar, BoundAnnotation]:
        """Bind each alias argument in the environment in which it was written."""

        bindings = dict(self.bindings)
        bindings.update(
            (parameter, BoundAnnotation(argument, self.bindings, expansion_trail))
            for parameter, argument in zip(parameters, arguments)
            if isinstance(parameter, TypeVar)
        )

        return bindings

    def find_match(
        self, annotations: tuple[object, ...], *, visited_aliases: frozenset[int] = frozenset()
    ) -> AnnotatedFieldInfo | None:
        """Return the first matching annotation using actual lexical parameter bindings."""

        bound = self.resolve()
        if bound is not self:
            visited_aliases = bound.expansion_trail

        annotation = bound.annotation
        origin = get_origin(annotation)
        alias = annotation if is_typealiastype(annotation) else origin

        if is_typealiastype(alias):
            if matches_requested_annotation(annotation, annotations):
                alias_match = AnnotatedFieldInfo(None, annotation, bound.metadata(), ())
            elif id(annotation) in visited_aliases:
                alias_match = None
            else:
                alias_match = BoundAnnotation(
                    alias.__value__,
                    bound.alias_bindings(alias.__type_params__, get_args(annotation), visited_aliases),
                ).find_match(annotations, visited_aliases=visited_aliases | {id(annotation)})

            return alias_match

        if origin in (Union, UnionType):
            for member in get_args(annotation):
                match = BoundAnnotation(member, bound.bindings).find_match(
                    annotations, visited_aliases=visited_aliases
                )
                if match is not None:
                    return match

            return None

        if origin is Annotated:
            inner_type, *metadata = get_args(annotation)
            matched_metadata = tuple(
                item for item in metadata if matches_requested_annotation(item, annotations)
            )

            if matched_metadata or matches_requested_annotation(annotation, annotations):
                return AnnotatedFieldInfo(None, annotation, tuple(metadata), matched_metadata)

            return BoundAnnotation(inner_type, bound.bindings).find_match(
                annotations, visited_aliases=visited_aliases
            )

        return (
            AnnotatedFieldInfo(None, annotation, (), ())
            if matches_requested_annotation(annotation, annotations)
            else None
        )

    def metadata(self, *, visited_aliases: frozenset[int] = frozenset()) -> tuple[object, ...]:
        """Return metadata outermost first, preserving each union branch's lexical context."""

        bound = self.resolve()
        if bound is not self:
            visited_aliases = bound.expansion_trail

        annotation = bound.annotation
        origin = get_origin(annotation)
        alias = annotation if is_typealiastype(annotation) else origin

        if is_typealiastype(alias):
            if id(annotation) in visited_aliases:
                return ()

            return BoundAnnotation(
                alias.__value__,
                bound.alias_bindings(alias.__type_params__, get_args(annotation), visited_aliases),
            ).metadata(visited_aliases=visited_aliases | {id(annotation)})

        if origin in (Union, UnionType):
            return tuple(
                item
                for member in get_args(annotation)
                for item in BoundAnnotation(member, bound.bindings).metadata(visited_aliases=visited_aliases)
            )

        if origin is Annotated:
            inner_type, *metadata = get_args(annotation)

            return (
                *metadata,
                *BoundAnnotation(inner_type, bound.bindings).metadata(visited_aliases=visited_aliases),
            )

        return ()


class FieldDeclaration(NamedTuple):
    """Store a field's extracted metadata and annotation holding nested metadata."""

    metadata: tuple[object, ...]
    annotation: object

    def matching_metadata(self, metadata_types: tuple[type[MetadataT], ...]) -> tuple[MetadataT, ...]:
        """Return metadata instances of requested types, outermost first."""

        return tuple(
            item
            for item in (*self.metadata, *BoundAnnotation(self.annotation).metadata())
            if isinstance(item, metadata_types)
        )
