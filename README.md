<div align="center" style="background:#fff3cd;border:1px solid #ffc107;border-radius:6px;padding:12px 16px;margin-bottom:16px">
  <strong>⚠ NOTE:</strong> This package does not depend on Pydantic and is pending a library rename.
</div>

# Pydantic Super Model

[![Coverage](https://img.shields.io/codecov/c/github/julien777z/pydantic-super-model?branch=main&label=Coverage)](https://codecov.io/gh/julien777z/pydantic-super-model)

`pydantic-super-model` is a small extension around Pydantic's `BaseModel` that adds:

- generic type introspection via `get_type()`
- lookup helpers for fields annotated with `typing.Annotated`
- a `FieldNotImplemented` marker for fields that must not be set yet

Import from the package root:

```python
from pydantic_super_model import AnnotatedFieldInfo, FieldNotImplemented, SuperModel
```

`pydantic_super_model.model` is no longer a supported import path.

## Installation

```bash
pip install pydantic-super-model
```

## Generic Example

```python
from typing import Generic, TypeVar

from pydantic_super_model import SuperModel

GenericType = TypeVar("GenericType")


class UserWithType(SuperModel, Generic[GenericType]):
    id: GenericType
    name: str


user = UserWithType[int](id=1, name="John Doe")

assert user.get_type() is int
```

## Annotated Field Example

```python
from typing import Annotated

from pydantic_super_model import SuperModel


class _PrimaryKeyAnnotation:
    pass


PrimaryKey = Annotated[int, _PrimaryKeyAnnotation]


class User(SuperModel):
    id: PrimaryKey
    name: str


user = User(id=1, name="John Doe")
field_info = user.get_annotated_fields(PrimaryKey)["id"]

assert field_info.value == 1
assert field_info.annotation == PrimaryKey
assert field_info.metadata == (_PrimaryKeyAnnotation,)
```

## API

### `get_annotated_fields(*annotations)`

Return a dictionary of field names to `AnnotatedFieldInfo` objects for fields whose type hints carry any requested annotation.

- Match by the full `Annotated[...]` alias or by metadata type
- Include falsy values such as `0`
- Include `None` only when the field was explicitly provided
- Omit unset default `None` values

```python
class UserOptional(SuperModel):
    id: PrimaryKey | None = None
    name: str


assert not UserOptional(name="A").get_annotated_fields(PrimaryKey)

field_info = UserOptional(id=None, name="B").get_annotated_fields(PrimaryKey)["id"]

assert field_info.value is None
assert field_info.metadata == (_PrimaryKeyAnnotation,)
```

Metadata instance matching also works:

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

### `get_annotated_field_value(annotation, allow_none=False, allow_undefined=False)`

Return the first matching `AnnotatedFieldInfo`.

```python
field_info = theme.get_annotated_field_value(ThemeColorOptions)

assert field_info is not None
assert field_info.value == "#7dd3fc"
```

If no matching field exists:

- raise `ValueError` by default
- return `None` when `allow_undefined=True`

If the matching field value is `None`:

- raise `ValueError` by default
- return the field info when `allow_none=True`

### `FieldNotImplemented`

Use `FieldNotImplemented` to mark fields that must not be set yet.

```python
from typing import Annotated

from pydantic_super_model import FieldNotImplemented, SuperModel


class Experimental(SuperModel):
    test_field: Annotated[int, FieldNotImplemented]
    name: str


Experimental(test_field=1, name="x")  # raises NotImplementedError


class ExperimentalOptional(SuperModel):
    test_field: Annotated[int | None, FieldNotImplemented] = None
    name: str


ExperimentalOptional(name="ok")
```

### `get_type()`

Return the concrete generic type parameter supplied to the model instance.

```python
assert UserWithType[int](id=1, name="Charlie").get_type() is int
```

## Development

Install dev dependencies:

```bash
pip install "pydantic-super-model[dev]"
```

Run the test suite:

```bash
pytest
```