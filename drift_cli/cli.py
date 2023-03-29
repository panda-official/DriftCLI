"""Main module"""
from importlib import metadata
from pathlib import Path
from typing import Optional

import click

from drift_cli.alias import alias
from drift_cli.export import export

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
    "--parallel",
    "-p",
    type=int,
    help="Number of parallel tasks to use, defaults to 10",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable debug logging",
)
@click.pass_context
def cli(
    ctx,
    config: Optional[Path] = None,
    parallel: Optional[int] = None,
    debug: bool = False,
):
    """CLI client for PANDA | Drift Platform"""
    if config is None:
        config = Path.home() / ".drift-cli" / "config.toml"

    if parallel is None:
        parallel = 10

    if not Path.exists(config):
        write_config(config, Config(aliases={}))

    ctx.obj["config_path"] = config
    ctx.obj["parallel"] = parallel
    ctx.obj["debug"] = debug


cli.add_command(alias, "alias")
cli.add_command(export, "export")
