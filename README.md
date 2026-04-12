# Pydantic Super Model

[![Coverage](https://img.shields.io/codecov/c/github/julien777z/pydantic-super-model?branch=main&label=Coverage)](https://codecov.io/gh/julien777z/pydantic-super-model)

A lightweight mixin for generic type introspection and `Annotated` field lookup. Works with any Python class, with optional Pydantic integration.

**Two classes:**

| Class | Base | Key extras |
|---|---|---|
| `SuperModelMixin` | Any class | Framework-agnostic annotation introspection |
| `SuperModelPydanticMixin` | Pydantic `BaseModel` | Auto `FieldNotImplemented` validation, omits unset default `None` values |

```python
from pydantic_super_model import AnnotatedFieldInfo, FieldNotImplemented, SuperModelMixin, SuperModelPydanticMixin
```

## Installation

```bash
pip install pydantic-super-model
```

## Quick Start

### With any Python class

```python
from typing import Annotated

from pydantic_super_model import SuperModelMixin


class PrimaryKeyAnnotation:
    pass


PrimaryKey = Annotated[int, PrimaryKeyAnnotation]


class User(SuperModelMixin):
    id: PrimaryKey
    name: str

    def __init__(self, id: PrimaryKey, name: str) -> None:
        self.id = id
        self.name = name


user = User(id=1, name="John Doe")
field_info = user.get_annotated_fields(PrimaryKey)["id"]

assert field_info.value == 1
assert field_info.annotation == PrimaryKey
assert field_info.metadata == (PrimaryKeyAnnotation,)
```

### With Pydantic

```python
from typing import Annotated

from pydantic_super_model import SuperModelPydanticMixin


class PrimaryKeyAnnotation:
    pass


PrimaryKey = Annotated[int, PrimaryKeyAnnotation]


class User(SuperModelPydanticMixin):
    id: PrimaryKey
    name: str


user = User(id=1, name="John Doe")
field_info = user.get_annotated_fields(PrimaryKey)["id"]

assert field_info.value == 1
assert field_info.annotation == PrimaryKey
assert field_info.metadata == (PrimaryKeyAnnotation,)
```

## API

### `get_annotated_fields(*annotations)`

Return a dictionary of field names to `AnnotatedFieldInfo` for fields whose type hints carry any requested annotation.

- Match by the full `Annotated[...]` alias or by metadata type
- Include falsy values such as `0`

**`SuperModelPydanticMixin` only:** unset default `None` values are omitted. Explicitly provided `None` is included.

```python
class UserOptional(SuperModelPydanticMixin):
    id: PrimaryKey | None = None
    name: str


# Unset default None is omitted
assert not UserOptional(name="A").get_annotated_fields(PrimaryKey)

# Explicitly provided None is included
field_info = UserOptional(id=None, name="B").get_annotated_fields(PrimaryKey)["id"]
assert field_info.value is None
```

**`SuperModelMixin`:** all `None` values are included regardless of whether they were explicitly set.

### `get_annotated_field_value(annotation, allow_none=False, allow_undefined=False)`

Return the first matching `AnnotatedFieldInfo`.

- Raises `ValueError` if no matching field exists (unless `allow_undefined=True`)
- Raises `ValueError` if the matched value is `None` (unless `allow_none=True`)

```python
field_info = user.get_annotated_field_value(PrimaryKey)

assert field_info.value == 1
```

### `get_type()`

Return the concrete generic type parameter supplied to the instance, or `None`.

```python
from typing import Generic, TypeVar

from pydantic_super_model import SuperModelMixin

GenericType = TypeVar("GenericType")


class UserWithType(SuperModelMixin, Generic[GenericType]):
    id: GenericType
    name: str

    def __init__(self, id: GenericType, name: str) -> None:
        self.id = id
        self.name = name


assert UserWithType[int](id=1, name="Charlie").get_type() is int
```

### `validate_not_implemented_fields()`

Reject fields annotated with `FieldNotImplemented`. Raises `NotImplementedError` if any such fields have values.

**`SuperModelPydanticMixin`:** called automatically on construction.

```python
from typing import Annotated

from pydantic_super_model import FieldNotImplemented, SuperModelPydanticMixin


class Experimental(SuperModelPydanticMixin):
    test_field: Annotated[int, FieldNotImplemented]
    name: str


Experimental(test_field=1, name="x")  # raises NotImplementedError
```

**`SuperModelMixin`:** call manually in `__init__` or `__post_init__`.

```python
from typing import Annotated

from pydantic_super_model import FieldNotImplemented, SuperModelMixin


class Experimental(SuperModelMixin):
    test_field: Annotated[int, FieldNotImplemented]
    name: str

    def __init__(self, test_field: int, name: str) -> None:
        self.test_field = test_field
        self.name = name
        self.validate_not_implemented_fields()


Experimental(test_field=1, name="x")  # raises NotImplementedError
```

### `AnnotatedFieldInfo`

A `NamedTuple` returned by `get_annotated_fields` and `get_annotated_field_value`:

| Field | Type | Description |
|---|---|---|
| `value` | `Any` | The field's current value |
| `annotation` | `object` | The full type annotation |
| `metadata` | `tuple[object, ...]` | All metadata from `Annotated` |
| `matched_metadata` | `tuple[object, ...]` | Only the metadata that matched the query |

### Metadata Instance Matching

When you pass a class (not an instance) to `get_annotated_fields`, it matches metadata by `isinstance`:

```python
from typing import Annotated

from pydantic_super_model import SuperModelPydanticMixin


class ThemeColorOptions:
    def __init__(self, *, palette: str, allow_gradients: bool) -> None:
        self.palette = palette
        self.allow_gradients = allow_gradients


ThemeColorField = Annotated[
    str,
    "theme_color",
    ThemeColorOptions(palette="northern-lights", allow_gradients=True),
]


class ThemeConfig(SuperModelPydanticMixin):
    accent_color: ThemeColorField


theme = ThemeConfig(accent_color="#7dd3fc")
field_info = theme.get_annotated_fields(ThemeColorOptions)["accent_color"]

assert isinstance(field_info.matched_metadata[0], ThemeColorOptions)
assert field_info.matched_metadata[0].palette == "northern-lights"
assert field_info.matched_metadata[0].allow_gradients is True
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
