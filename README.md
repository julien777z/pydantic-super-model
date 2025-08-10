# Super Model for Pydantic

I created this package because I needed a centralized place
for a Pydantic BaseModel that can 1) return the generic type of the BaseModel
and 2) return which field(s) have a certain Annotation.

## Installation

Install with [pip](https://pip.pypa.io/en/stable/)
```bash
pip install super_model
```

## Features

- Generic support
- Able to retrieve field(s) with a specific Annotation

## Generic Example

```python

from super_model import BaseModel

class UserWithType[T](BaseModel):
    """User model with a generic type."""

    id: T
    name: str

user = UserWithType[int](id=1, name="John Doe")

user_type = user.get_type() # int
```

## Annotation Example

```python

from typing import Annotated
from super_model import BaseModel


class _PrimaryKeyAnnotation:
    pass

PrimaryKey = Annotated[int, _PrimaryKeyAnnotation]

class UserWithAnnotation(BaseModel):
    """User model with an Annotation for a field."""

    id: PrimaryKey
    name: str

user = UserWithAnnotation(id=1, name="John Doe")

annotations = user.get_annotated_fields(PrimaryKey)
# {"id": 1}
```