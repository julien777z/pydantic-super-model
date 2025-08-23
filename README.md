# Super Model for Pydantic

[![Coverage](https://img.shields.io/codecov/c/github/julien777z/pydantic-super-model?branch=main&label=Coverage)](https://codecov.io/gh/julien777z/pydantic-super-model)

A lightweight extension of Pydantic's `BaseModel` that adds generic type introspection and retrieval of fields annotated with `typing.Annotated`.

## Installation

Install with [pip](https://pip.pypa.io/en/stable/)
```bash
pip install pydantic-super-model
```

## Features

- Generic support
- Able to retrieve field(s) with a specific Annotation

## Generic Example

```python

from super_model import SuperModel

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
from super_model import SuperModel


class _PrimaryKeyAnnotation:
    pass

PrimaryKey = Annotated[int, _PrimaryKeyAnnotation]

class UserWithAnnotation(SuperModel):
    """User model with an Annotation for a field."""

    id: PrimaryKey
    name: str

user = UserWithAnnotation(id=1, name="John Doe")

annotations = user.get_annotated_fields(PrimaryKey)
# {"id": 1}
```

## Documentation

### Get Annotated Fields

`SuperModel.get_annotated_fields(*annotations)` returns a dict of field names to values for fields whose type hints carry any of the provided annotations (either the `Annotated[...]` alias or the meta annotation type).

It includes falsy values (like `0` or an empty string) and includes `None` only when the field was explicitly provided. Unset default `None` values are omitted.

```python
from typing import Annotated
from super_model import SuperModel

class _PrimaryKey:
    pass

PrimaryKey = Annotated[int, _PrimaryKey]

class User(SuperModel):
    id: PrimaryKey
    name: str

u = User(id=1, name="Jane")

assert u.get_annotated_fields(PrimaryKey) == {"id": 1}
```

Explicit None vs. unset default:

```python
class UserOptional(SuperModel):
    id: PrimaryKey | None = None
    name: str

# Unset default None is omitted
assert not UserOptional(name="A").get_annotated_fields(PrimaryKey)

# Explicit None is included
assert UserOptional(id=None, name="B").get_annotated_fields(PrimaryKey) == {"id": None}
```

### FieldNotImplemented Annotation

You can use the `FieldNotImplemented` annotation to mark fields that should not be set:

```python
from typing import Annotated
from super_model import SuperModel, FieldNotImplemented

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
from super_model import SuperModel

class UserWithType[T](SuperModel):
    id: T
    name: str

u = UserWithType[int](id=1, name="Charlie")

assert u.get_type() is int
```

## Run Tests

* Install with the `dev` extra: `pip install pydantic-super-model[dev]`
* Run tests with `pytest .`