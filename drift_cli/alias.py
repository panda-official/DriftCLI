"""Alias commands"""
from typing import Optional

import click
from click import Abort

from drift_cli.config import Config, read_config, write_config, Alias
from drift_cli.utils.consoles import console, error_console
from drift_cli.utils.error import error_handle
from drift_cli.utils.helpers import get_alias


@click.group()
@click.pass_context
def alias(ctx):
    """Commands to manage aliases"""
    ctx.obj["conf"] = read_config(ctx.obj["config_path"])


@alias.command()
@click.pass_context
def ls(ctx):
    """Print list of aliases"""
    for name, _ in ctx.obj["conf"].aliases.items():
        console.print(name)


@alias.command()
@click.argument("name")
@click.pass_context
def show(ctx, name: str):
    """Show alias configuration"""
    alias_: Alias = get_alias(ctx.obj["config_path"], name)
    console.print(f"[bold]Address[/bold]:  {alias_.address}")
    console.print(f"[bold]Bucket[/bold] :  {alias_.bucket}")


@alias.command()
@click.argument("name")
@click.option(
    "--address", "-A", help="Address of Drift instance, can be IP or hostname"
)
@click.option("--password", "-p", help="Password for Drift instance")
@click.option("--bucket", "-b", help="Bucket to use, defaults to 'data'")
@click.pass_context
def add(
    ctx,
    name: str,
    address: Optional[str],
    password: Optional[str],
    bucket: Optional[str],
):
    """Add a new alias with NAME"""
    conf: Config = ctx.obj["conf"]
    if name in conf.aliases:
        error_console.print(f"Alias '{name}' already exists")
        raise Abort()

    if address is None or len(address) == 0:
        address = click.prompt("IP or Hostname", type=str)
    if password is None:
        password = click.prompt("Password", type=str, hide_input=True)
    if bucket is None:
        bucket = click.prompt("Bucket", type=str, default="data")

    with error_handle(ctx.obj["debug"]):
        entry = Alias(address=address, password=password, bucket=bucket)

        conf.aliases[name] = entry
        write_config(ctx.obj["config_path"], conf)


@alias.command()
@click.argument("name")
@click.pass_context
def rm(ctx, name: str):
    """
    Remove alias with NAME
    """
    # Check if name exists
    conf: Config = ctx.obj["conf"]
    _ = get_alias(ctx.obj["config_path"], name)

    conf.aliases.pop(name)
    write_config(ctx.obj["config_path"], conf)
