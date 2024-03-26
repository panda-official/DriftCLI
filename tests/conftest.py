"""Common fixtures"""

from functools import partial
from pathlib import Path
from tempfile import gettempdir
from typing import Callable, Optional, List, Any

import pytest
from click.testing import CliRunner, Result

from drift_cli.cli import cli


class AsyncIter:  # pylint: disable=too-few-public-methods
    """Helper class for efficient mocking"""

    def __init__(self, items: Optional[List[Any]] = None):
        self.items = items if items else []

    async def __aiter__(self):
        for item in self.items:
            yield item


@pytest.fixture(name="runner")
def _make_runner() -> Callable[[str], Result]:
    runner = CliRunner()
    return partial(runner.invoke, cli, obj={})


@pytest.fixture(name="conf")
def _make_conf() -> Path:
    path = Path(gettempdir()) / "config.toml"
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture(name="address")
def _make_url() -> str:
    return "127.0.0.1"


@pytest.fixture(name="set_alias")
def _set_alias(runner, conf, address):
    runner(f"-c {conf} alias add test", input=f"{address}\npassword\ndata\n")
