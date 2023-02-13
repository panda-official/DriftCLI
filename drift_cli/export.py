"""Export Command"""
import asyncio
from asyncio import new_event_loop as loop

import click
from drift_client import DriftClient

from drift_cli.config import Alias
from drift_cli.config import read_config
from drift_cli.export_impl.raw import export_raw
from drift_cli.utils.error import error_handle
from drift_cli.utils.helpers import (
    parse_path,
)


start_option = click.option(
    "--start",
    help="Export records with timestamps newer than this time point in ISO format",
)

stop_option = click.option(
    "--stop",
    help="Export records  with timestamps older than this time point in ISO format",
)


@click.group()
def export():
    """Export data from a bucket somewhere else"""


@export.command()
@click.argument("src")
@click.argument("dest")
@stop_option
@start_option
@click.pass_context
def raw(
    ctx,
    src: str,
    dest: str,
    start: str,
    stop: str,
):  # pylint: disable=too-many-arguments
    """Export data from SRC bucket to DST folder

    SRC should be in the format of ALIAS/BUCKET_NAME.
    DST should be a path to a folder.

    As result, the folder will contain a folder for each entry in the bucket.
    Each entry folder will contain a file for each record
    in the entry with the timestamp as the name.
    """

    alias_name, _ = parse_path(src)
    alias: Alias = read_config(ctx.obj["config_path"]).aliases[alias_name]

    loop = asyncio.get_event_loop()
    run = loop.run_until_complete
    client = DriftClient(alias.address, alias.password, loop=loop)

    with error_handle():
        run(
            export_raw(
                client,
                dest,
                parallel=ctx.obj["parallel"],
                start=start,
                stop=stop,
            )
        )
