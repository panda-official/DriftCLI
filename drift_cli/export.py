"""Export Command"""
import asyncio

import click
from click import Abort
from drift_client import DriftClient

from drift_cli.config import Alias
from drift_cli.config import read_config
from drift_cli.export_impl.raw import export_raw
from drift_cli.utils.consoles import error_console
from drift_cli.utils.error import error_handle
from drift_cli.utils.helpers import (
    parse_path,
)

start_option = click.option(
    "--start",
    help="Export records with timestamps newer than this time point in ISO format"
    " e.g. 2023-01-01T00:00:00.000Z",
)

stop_option = click.option(
    "--stop",
    help="Export records  with timestamps older than this time point in ISO format"
    " e.g 2023-01-01T00:00:00.000Z",
)

topics_option = click.option(
    "--topics",
    help="Export only these topics, separated by comma. You can use * as a wildcard",
    default="",
)


@click.group()
def export():
    """Export data from a bucket somewhere else"""


@export.command()
@click.argument("src")
@click.argument("dest")
@stop_option
@start_option
@topics_option
@click.option(
    "--csv",
    help="Export data as CSV instead of raw data (only for timeseries)",
    default=False,
    is_flag=True,
)
@click.option(
    "--jpeg",
    help="Export data as JPEG instead of raw data (only for images)",
    default=False,
    is_flag=True,
)
@click.pass_context
def raw(
    ctx,
    src: str,
    dest: str,
    start: str,
    stop: str,
    topics: str,
    csv: bool,
    jpeg: bool,
):  # pylint: disable=too-many-arguments
    """Export data from SRC bucket to DST folder

    SRC should be in the format of ALIAS/BUCKET_NAME.
    DST should be a path to a folder.

    As result, the folder will contain a folder for each entry in the bucket.
    Each entry folder will contain a file for each record
    in the entry with the timestamp as the name.
    """
    if start is None or stop is None:
        error_console.print("Error: --start and --stop are required")
        raise Abort()

    if csv and jpeg:
        error_console.print("Error: --csv and --jpeg are mutually exclusive")
        raise Abort()

    alias_name, _ = parse_path(src)
    alias: Alias = read_config(ctx.obj["config_path"]).aliases[alias_name]

    loop = asyncio.get_event_loop()
    run = loop.run_until_complete
    client = DriftClient(alias.address, alias.password, loop=loop)

    with error_handle(ctx.obj["debug"]):
        run(
            export_raw(
                client,
                dest,
                parallel=ctx.obj["parallel"],
                topics=topics.split(","),
                start=start,
                stop=stop,
                csv=csv,
                jpeg=jpeg,
            )
        )
