# Super Model for Pydantic

I created this package because I needed a centralized place
for a Pydantic BaseModel that can 1) return the generic type of the BaseModel
and 2) return which field(s) have a certain Annotation.

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

## Run Tests

* Install with the `dev` extra: `pip install pydantic-super-model[dev]`
* Run tests with `pytest .`