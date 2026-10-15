import sys

import pytest

from pydantic_super_model import SuperModelMixin
from tests.models.plain_user import PlainAliasedColumnConfig
from tests.models.user import AliasedColumnConfig

collect_ignore_glob: list[str] = [] if sys.version_info >= (3, 12) else ["test_native_aliases.py"]


@pytest.fixture(
    name="aliased_model",
    params=[AliasedColumnConfig, PlainAliasedColumnConfig],
    ids=["pydantic", "plain"],
)
def aliased_model_fixture(request: pytest.FixtureRequest) -> type[SuperModelMixin]:
    """Return each model declaring named alias fields."""

    return request.param
