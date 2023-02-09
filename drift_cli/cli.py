"""Main module"""
from importlib import metadata
from pathlib import Path
from typing import Optional

import click

from drift_cli.alias import alias
from drift_cli.config import write_config, Config


@click.group()
@click.version_option(metadata.version("drift-cli"))
@click.option(
    "--config",
    "-c",
    type=Path,
    help="Path to config file. Default ${HOME}/drift-cli/config.toml",
)
@click.option(
    "--timeout",
    "-t",
    type=int,
    help="Timeout for requests in seconds. Default 5",
)
@click.option(
    "--parallel",
    "-p",
    type=int,
    help="Number of parallel tasks to use, defaults to 10",
)
@click.pass_context
def cli(
    ctx,
    config: Optional[Path] = None,
    timeout: Optional[int] = None,
    parallel: Optional[int] = None,
):
    """CLI client for PANDA | Drift Platform"""
    if config is None:
        config = Path.home() / ".drift-cli" / "config.toml"

    if timeout is None:
        timeout = 5

    if parallel is None:
        parallel = 10

    if not Path.exists(config):
        write_config(config, Config(aliases={}))

    ctx.obj["config_path"] = config
    ctx.obj["timeout"] = timeout
    ctx.obj["parallel"] = parallel


cli.add_command(alias, "alias")
