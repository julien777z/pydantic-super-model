# Pydantic Super Model

Generic type introspection and `Annotated` field lookup for any Python class, with optional Pydantic integration.

[![Coverage](https://img.shields.io/codecov/c/github/julien777z/pydantic-super-model?branch=main&label=Coverage)](https://codecov.io/gh/julien777z/pydantic-super-model)

## Features

- Look up fields by their full `Annotated` alias or by a metadata type, matching metadata instances with `isinstance`.
- Resolve metadata from the class, with no instance, wherever it lives: hoisted onto the field, nested inside a union member, or inside a nested `Annotated`.
- Read the concrete generic type parameter an instance was built with.
- Reject fields marked as intentionally not implemented, checked automatically on Pydantic models.
- Works with any Python class; the Pydantic mixin adds that validation and unset-`None` filtering.
- Typed throughout, with a PEP 561 `py.typed` marker.

## Installation

```bash
pip install pydantic-super-model
```

## Mixins

| Mixin | Base | Adds |
|---|---|---|
| `SuperModelMixin` | any Python class | annotation introspection and generic type resolution |
| `SuperModelPydanticMixin` | Pydantic `BaseModel` | automatic `FieldNotImplemented` validation, omits unset default `None` values |

The examples below use `SuperModelPydanticMixin`. Each one works the same through `SuperModelMixin`, which reads values straight off the instance.

## Quick Start

Annotate a field with any metadata object, then ask an instance for it:

```python
from typing import Annotated

from pydantic_super_model import SuperModelPydanticMixin


class PrimaryKeyAnnotation:
    pass


PrimaryKey = Annotated[int, PrimaryKeyAnnotation]


class User(SuperModelPydanticMixin):
    id: PrimaryKey
    name: str


field_info = User(id=1, name="John Doe").get_annotated_fields(PrimaryKey)["id"]

field_info.value        # 1
field_info.annotation   # PrimaryKey
field_info.metadata     # (PrimaryKeyAnnotation,)
```

A plain class carries the same API once it inherits `SuperModelMixin`:

```python
from pydantic_super_model import SuperModelMixin


class Account(SuperModelMixin):
    id: PrimaryKey

    def __init__(self, id: PrimaryKey) -> None:
        self.id = id


Account(id=1).get_annotated_fields(PrimaryKey)["id"].value   # 1
```

## Annotated Field Lookup

`get_annotated_fields` returns the matching fields as a mapping of names to `AnnotatedFieldInfo`. A query matches either the full `Annotated[...]` alias or a metadata type, and falsy values such as `0` are included:

```python
user = User(id=0, name="Zero")

user.get_annotated_fields(PrimaryKey)["id"].value             # 0
user.get_annotated_fields(PrimaryKeyAnnotation)["id"].value   # 0, matched by metadata type
```

`get_annotated_field_value` returns the first match instead of a mapping. It raises `ValueError` when nothing matches, unless `allow_undefined=True`, and when the matched value is `None`, unless `allow_none=True`:

```python
user.get_annotated_field_value(PrimaryKey).value   # 0
```

Querying by class matches metadata **instances**, and `matched_metadata` carries the ones that matched:

```python
class ThemeColorOptions:
    def __init__(self, *, palette: str) -> None:
        self.palette = palette


class Theme(SuperModelPydanticMixin):
    accent_color: Annotated[str, "theme_color", ThemeColorOptions(palette="northern-lights")]


field_info = Theme(accent_color="#7dd3fc").get_annotated_fields(ThemeColorOptions)["accent_color"]

field_info.metadata[0]                    # "theme_color"
field_info.matched_metadata[0].palette    # "northern-lights"
```

On `SuperModelPydanticMixin` a field left at its default `None` is omitted, while a `None` passed explicitly is kept. `SuperModelMixin` keeps every `None`:

```python
class OptionalUser(SuperModelPydanticMixin):
    id: PrimaryKey | None = None


OptionalUser().get_annotated_fields(PrimaryKey)          # {}, unset default
OptionalUser(id=None).get_annotated_fields(PrimaryKey)   # {"id": ...}, explicit None
```

## Class-Level Metadata

Three classmethods answer "which fields of this class carry metadata X" with no instance in hand. Metadata is found both where Pydantic hoists it onto the field, for a bare `Annotated[...]`, and where it stays nested inside a union member or a nested `Annotated`:

```python
class ColumnOptions:
    def __init__(self, *, name: str) -> None:
        self.name = name


class Record(SuperModelPydanticMixin):
    identifier: Annotated[str, ColumnOptions(name="identifier")]
    label: Annotated[str, ColumnOptions(name="label")] | None = None
    plain: str = ""


Record.field_metadata("identifier", ColumnOptions)[0].name   # "identifier"
Record.field_metadata("plain", ColumnOptions)                # ()
Record.first_field_metadata("label", ColumnOptions).name     # "label"
Record.first_field_metadata("plain", ColumnOptions)          # None
Record.field_names_with_metadata(ColumnOptions)              # frozenset({"identifier", "label"})
```

`field_metadata` takes any number of metadata types and returns every instance of them in declaration order. A field the class does not declare raises `KeyError`.

`collect_annotated_fields` accepts a class as well as an instance. Given a class it resolves the type hints, so every `value` is `None`:

```python
from pydantic_super_model import collect_annotated_fields

collect_annotated_fields(Record, ColumnOptions)["identifier"].value   # None
```

## Generic Type Resolution

`get_type` returns the concrete generic parameter the instance was built with, or `None`:

```python
from typing import Generic, TypeVar

from pydantic_super_model import SuperModelMixin

GenericType = TypeVar("GenericType")


class Box(SuperModelMixin, Generic[GenericType]):
    def __init__(self, value: GenericType) -> None:
        self.value = value


Box[int](value=1).get_type()   # <class 'int'>
Box(value=1).get_type()        # None, no parameter supplied
```

## Not-Implemented Fields

`FieldNotImplemented` marks a field that should be removed rather than used. `SuperModelPydanticMixin` checks for it on construction:

```python
from pydantic_super_model import FieldNotImplemented, SuperModelPydanticMixin


class Experimental(SuperModelPydanticMixin):
    test_field: Annotated[int, FieldNotImplemented]


Experimental(test_field=1)   # raises NotImplementedError
```

On a plain class, call `validate_not_implemented_fields()` yourself, usually at the end of `__init__`.

## AnnotatedFieldInfo

The `NamedTuple` returned by `get_annotated_fields` and `get_annotated_field_value`:

| Field | Type | Description |
|---|---|---|
| `value` | `Any` | The field's current value |
| `annotation` | `object` | The full type annotation |
| `metadata` | `tuple[object, ...]` | All metadata from `Annotated` |
| `matched_metadata` | `tuple[object, ...]` | Only the metadata that matched the query |

## Local Development

```bash
poetry install --all-extras              # install
poetry run pytest                        # run the tests
poetry run black .                       # format
poetry run isort .                       # sort imports
poetry run pylint pydantic_super_model   # lint
```
