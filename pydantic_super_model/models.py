from __future__ import annotations

from collections.abc import Iterator, Mapping
from types import MappingProxyType, UnionType
from typing import Annotated, Any, NamedTuple, TypeVar, Union, get_args, get_origin

from typing_inspection.typing_objects import is_typealiastype, is_typevartuple

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


class AnnotatedFieldInfo(NamedTuple):
    """Store a matched annotated field value and its metadata."""

    value: Any
    annotation: object
    metadata: tuple[object, ...]
    matched_metadata: tuple[object, ...]


class BoundAnnotation(NamedTuple):
    """Store an annotation with the lexical bindings and alias expansions that supplied it."""

    annotation: object
    bindings: Mapping[TypeVar, BoundAnnotation] = MappingProxyType({})
    expansion_trail: frozenset[int] = frozenset()

    def argument_bindings(self, parameters: tuple[object, ...]) -> dict[TypeVar, BoundAnnotation]:
        """Bind each alias type parameter to the argument written for it, in the caller's bindings."""

        arguments = get_args(self.annotation)
        variadic_index = next(
            (index for index, parameter in enumerate(parameters) if is_typevartuple(parameter)),
            len(parameters),
        )
        leading = parameters[:variadic_index]
        trailing = parameters[variadic_index + 1 :]

        positional_pairs = zip(
            (*leading, *trailing),
            (*arguments[: len(leading)], *arguments[len(arguments) - len(trailing) :]),
        )

        return {
            parameter: BoundAnnotation(argument, self.bindings, self.expansion_trail)
            for parameter, argument in positional_pairs
            if isinstance(parameter, TypeVar)
        }

    def walk(self) -> Iterator[BoundAnnotation]:
        """Yield each node outermost first, expanding aliases and union members in their own bindings."""

        bound = self

        while isinstance(bound.annotation, TypeVar) and bound.annotation in bound.bindings:
            bound = bound.bindings[bound.annotation]

        yield bound

        annotation = bound.annotation
        origin = get_origin(annotation)
        alias = annotation if is_typealiastype(annotation) else origin

        if is_typealiastype(alias):
            if id(annotation) not in bound.expansion_trail:
                yield from BoundAnnotation(
                    alias.__value__,
                    bound.argument_bindings(alias.__type_params__),
                    bound.expansion_trail | {id(annotation)},
                ).walk()
        elif origin in (Union, UnionType):
            for member in get_args(annotation):
                yield from bound._replace(annotation=member).walk()
        elif origin is Annotated:
            yield from bound._replace(annotation=get_args(annotation)[0]).walk()

    def nested_metadata(self) -> tuple[object, ...]:
        """Return every metadata item the annotation carries, outermost first."""

        return tuple(
            item
            for node in self.walk()
            if get_origin(node.annotation) is Annotated
            for item in get_args(node.annotation)[1:]
        )

    def find_match(self, annotations: tuple[object, ...]) -> AnnotatedFieldInfo | None:
        """Return the outermost node matching a requested annotation."""

        for node in self.walk():
            annotation = node.annotation
            origin = get_origin(annotation)
            metadata = get_args(annotation)[1:] if origin is Annotated else ()
            matched_metadata = tuple(
                item for item in metadata if matches_requested_annotation(item, annotations)
            )

            if not matched_metadata and not matches_requested_annotation(annotation, annotations):
                continue

            if is_typealiastype(annotation) or is_typealiastype(origin):
                metadata = node.nested_metadata()

            return AnnotatedFieldInfo(None, annotation, tuple(metadata), matched_metadata)

        return None


class FieldDeclaration(NamedTuple):
    """Store a field's extracted metadata and annotation holding nested metadata."""

    metadata: tuple[object, ...]
    annotation: object

    def matching_metadata(self, metadata_types: tuple[type[MetadataT], ...]) -> tuple[MetadataT, ...]:
        """Return metadata instances of requested types, outermost first."""

        return tuple(
            item
            for item in (*self.metadata, *BoundAnnotation(self.annotation).nested_metadata())
            if isinstance(item, metadata_types)
        )
