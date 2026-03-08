# Super Model for Pydantic

[![Coverage](https://img.shields.io/codecov/c/github/julien777z/pydantic-super-model?branch=main&label=Coverage)](https://codecov.io/gh/julien777z/pydantic-super-model)

A lightweight extension of Pydantic's `BaseModel` that adds generic type introspection and retrieval of fields annotated with `typing.Annotated`, including their metadata.

## Installation

Install with [pip](https://pip.pypa.io/en/stable/)
```bash
pip install pydantic-super-model
```

## Features

- Generic support
- Able to retrieve field(s) with a specific annotation and metadata

## Generic Example

```python

from pydantic_super_model import SuperModel

class UserWithType[T](SuperModel):
    """User model with a generic type."""

    id: T
    name: str

user = UserWithType[int](id=1, name="John Doe")

user_type = user.get_type() # int
```

## Annotation Example

```python

from typing import Annotated
from pydantic_super_model import SuperModel


class _PrimaryKeyAnnotation:
    pass

PrimaryKey = Annotated[int, _PrimaryKeyAnnotation]

class UserWithAnnotation(SuperModel):
    """User model with an Annotation for a field."""

    id: PrimaryKey
    name: str

user = UserWithAnnotation(id=1, name="John Doe")

annotations = user.get_annotated_fields(PrimaryKey)

field_info = annotations["id"]
assert field_info.value == 1
assert field_info.metadata == (_PrimaryKeyAnnotation,)
```

## Documentation

### Get Annotated Fields

`SuperModel.get_annotated_fields(*annotations)` returns a dict of field names to `AnnotatedFieldInfo` objects for fields whose type hints carry any of the provided annotations (either the `Annotated[...]` alias or the meta annotation type).

It includes falsy values (like `0` or an empty string) and includes `None` only when the field was explicitly provided. Unset default `None` values are omitted.

```python
from typing import Annotated
from pydantic_super_model import SuperModel

class _PrimaryKey:
    pass

PrimaryKey = Annotated[int, _PrimaryKey]

class User(SuperModel):
    id: PrimaryKey
    name: str

u = User(id=1, name="Jane")

field_info = u.get_annotated_fields(PrimaryKey)["id"]

assert field_info.value == 1
assert field_info.annotation == PrimaryKey
assert field_info.metadata == (_PrimaryKey,)
```

Explicit None vs. unset default:

```python
class UserOptional(SuperModel):
    id: PrimaryKey | None = None
    name: str

# Unset default None is omitted
assert not UserOptional(name="A").get_annotated_fields(PrimaryKey)

# Explicit None is included
field_info = UserOptional(id=None, name="B").get_annotated_fields(PrimaryKey)["id"]

assert field_info.value is None
assert field_info.metadata == (_PrimaryKey,)
```

Metadata-instance matching:

```python
from typing import Annotated

from pydantic_super_model import SuperModel


class ThemeColorOptions:
    def __init__(self, *, palette: str, allow_gradients: bool) -> None:
        self.palette = palette
        self.allow_gradients = allow_gradients


ThemeColorField = Annotated[
    str,
    "theme_color",
    ThemeColorOptions(palette="northern-lights", allow_gradients=True),
]


class ThemeConfig(SuperModel):
    accent_color: ThemeColorField


theme = ThemeConfig(accent_color="#7dd3fc")
field_info = theme.get_annotated_fields(ThemeColorOptions)["accent_color"]

assert isinstance(field_info.matched_metadata[0], ThemeColorOptions)
assert field_info.matched_metadata[0].palette == "northern-lights"
assert field_info.matched_metadata[0].allow_gradients is True
```

Use `get_annotated_field_value(...)` when you want the first matching `AnnotatedFieldInfo` directly.

```python
field_info = theme.get_annotated_field_value(ThemeColorOptions)

assert field_info is not None
assert field_info.value == "#7dd3fc"
assert field_info.matched_metadata[0].palette == "northern-lights"
```

### FieldNotImplemented Annotation

You can use the `FieldNotImplemented` annotation to mark fields that should not be set. An example
use case are experimental fields that you intend on implementing later.

```python
from typing import Annotated
from pydantic_super_model import SuperModel, FieldNotImplemented

class Experimental(SuperModel):
    test_field: Annotated[int, FieldNotImplemented]
    name: str

# Raises NotImplementedError because the field is provided
Experimental(test_field=1, name="x")

# Optional + unset default is allowed
class ExperimentalOptional(SuperModel):
    test_field: Annotated[int | None, FieldNotImplemented] = None
    name: str

ExperimentalOptional(name="ok")  # ok (field is unset)
```

### Generics

Use `get_type()` to retrieve the concrete generic type parameter supplied at instantiation time.

```python
from pydantic_super_model import SuperModel

class UserWithType[T](SuperModel):
    id: T
    name: str

u = UserWithType[int](id=1, name="Charlie")

assert u.get_type() is int
```

## Run Tests

* Install with the `dev` extra: `pip install pydantic-super-model[dev]`
* Run tests with `pytest .`