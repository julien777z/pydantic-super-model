from __future__ import annotations

from collections.abc import Iterator, Mapping
from types import MappingProxyType, UnionType
from typing import Annotated, Any, Final, NamedTuple, TypeVar, Union, get_args, get_origin

from typing_inspection.typing_objects import is_nodefault, is_typealiastype, is_typevartuple

MetadataT = TypeVar("MetadataT")
UNDECLARED_DEFAULT: Final[object] = object()


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
        """Bind each alias type parameter to the argument written for it, or to its default."""

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
        bindings = {
            parameter: BoundAnnotation(argument, self.bindings, self.expansion_trail)
            for parameter, argument in positional_pairs
            if isinstance(parameter, TypeVar)
        }

        for parameter in parameters:
            default = getattr(parameter, "__default__", UNDECLARED_DEFAULT)

            if parameter in bindings or default is UNDECLARED_DEFAULT or is_nodefault(default):
                continue

            bindings[parameter] = BoundAnnotation(
                default, MappingProxyType(dict(bindings)), self.expansion_trail
            )

        return bindings

    def resolved(self) -> BoundAnnotation:
        """Return the annotation a bound type parameter stands for."""

        bound = self

        while isinstance(bound.annotation, TypeVar) and bound.annotation in bound.bindings:
            bound = bound.bindings[bound.annotation]

        return bound

    def concrete_annotation(self) -> object:
        """Return the annotation with its bound type parameters substituted."""

        if get_origin(self.annotation) is None:
            return self.annotation

        parameters = getattr(self.annotation, "__parameters__", ())

        if not any(parameter in self.bindings for parameter in parameters) or not all(
            isinstance(parameter, TypeVar) for parameter in parameters
        ):
            return self.annotation

        return self.annotation[
            tuple(
                (
                    self.bindings[parameter].resolved().concrete_annotation()
                    if parameter in self.bindings
                    else parameter
                )
                for parameter in parameters
            )
        ]

    def unwrapped(self) -> tuple[tuple[object, ...], BoundAnnotation]:
        """Return an Annotated chain's metadata, innermost first, and the annotation it wraps."""

        metadata: tuple[object, ...] = ()
        bound = self

        while get_origin(bound.annotation) is Annotated:
            inner_type, *items = get_args(bound.annotation)
            metadata = (*items, *metadata)
            bound = bound._replace(annotation=inner_type).resolved()

        return metadata, bound

    def walk(self) -> Iterator[BoundAnnotation]:
        """Yield each node outermost first, expanding aliases and union members in their own bindings."""

        bound = self.resolved()

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
            yield from bound.unwrapped()[1].walk()

    def nested_metadata(self) -> tuple[object, ...]:
        """Return every metadata item the annotation carries, outermost layer first."""

        return tuple(item for node in self.walk() for item in node.unwrapped()[0])

    def candidates(self) -> tuple[AnnotationCandidate, ...]:
        """Return each walked node as a match candidate, outermost first."""

        candidates: list[AnnotationCandidate] = []

        for node in self.walk():
            metadata = node.unwrapped()[0]
            reported_metadata = (
                metadata if get_origin(node.annotation) is Annotated else node.nested_metadata()
            )

            candidates.append(
                AnnotationCandidate(node.annotation, metadata, node.concrete_annotation(), reported_metadata)
            )

        return tuple(candidates)

    def find_match(self, annotations: tuple[object, ...]) -> AnnotatedFieldInfo | None:
        """Return the outermost node matching a requested annotation."""

        return first_candidate_match(self.candidates(), annotations)


class AnnotationCandidate(NamedTuple):
    """Store one walked annotation node and the metadata a match on it reports."""

    annotation: object
    metadata: tuple[object, ...]
    concrete_annotation: object
    reported_metadata: tuple[object, ...]

    def match(self, annotations: tuple[object, ...]) -> AnnotatedFieldInfo | None:
        """Return this node's match for a requested annotation, or None."""

        matched_metadata = tuple(
            item for item in self.metadata if matches_requested_annotation(item, annotations)
        )

        if not matched_metadata and not matches_requested_annotation(self.annotation, annotations):
            return None

        return AnnotatedFieldInfo(None, self.concrete_annotation, self.reported_metadata, matched_metadata)


def first_candidate_match(
    candidates: tuple[AnnotationCandidate, ...],
    annotations: tuple[object, ...],
) -> AnnotatedFieldInfo | None:
    """Return the first candidate's match for a requested annotation, or None."""

    return next(
        (match for candidate in candidates if (match := candidate.match(annotations)) is not None),
        None,
    )


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
