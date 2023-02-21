"""Helper functions"""
import asyncio
import signal
import time
from asyncio import Semaphore, Queue
from concurrent.futures import Executor
from datetime import datetime
from pathlib import Path
from typing import Tuple, List

from click import Abort
from drift_client import DriftClient
from rich.progress import Progress

from drift_cli.config import read_config, Alias
from drift_cli.utils.consoles import error_console
from drift_cli.utils.humanize import pretty_size

signal_queue = Queue()


def get_alias(config_path: Path, name: str) -> Alias:
    """Helper method to parse alias from config"""
    conf = read_config(config_path)

    if name not in conf.aliases:
        error_console.print(f"Alias '{name}' doesn't exist")
        raise Abort()
    alias_: Alias = conf.aliases[name]
    return alias_


def parse_path(path) -> Tuple[str, str]:
    """Parse path ALIAS/RESOURCE"""
    args = path.split("/")
    if len(args) > 2:
        raise RuntimeError(
            f"Path {path} has wrong format. It must be 'ALIAS/BUCKET_NAME'"
        )

    if len(args) == 1:
        args.append("panda")

    return tuple(args)


async def read_topic(
    pool: Executor,
    client: DriftClient,
    topic: str,
    progress: Progress,
    sem: Semaphore,
    **kwargs,
):  # pylint: disable=too-many-locals
    """Read records from entry and show progress
    Args:
        client: Drift client
        topic: Topic name
        progress (Progress): Progress bar to show progress
        sem (Semaphore): Semaphore to limit parallelism
    Keyword Args:
        start (Optional[datetime]): Start time point
        stop (Optional[datetime]): Stop time point
        timeout (int): Timeout for read operation
    Yields:
        Record: Record from entry
    """

    def _to_timestamp(date: str) -> float:
        return datetime.fromisoformat(date.replace("Z", "+00:00")).timestamp()

    start = _to_timestamp(kwargs["start"])
    stop = _to_timestamp(kwargs["stop"])

    last_time = start
    task = progress.add_task(f"Topic '{topic}' waiting", total=stop - start)
    async with sem:
        exported_size = 0
        count = 0
        stats = []
        speed = 0

        loop = asyncio.get_running_loop()

        def stop_signal():
            signal_queue.put_nowait("stop")

        loop.add_signal_handler(signal.SIGINT, stop_signal)
        loop.add_signal_handler(signal.SIGTERM, stop_signal)

        packages = await loop.run_in_executor(
            pool, client.get_package_names, topic, start, stop
        )
        for package in sorted(packages):
            drift_pkg = await loop.run_in_executor(pool, client.get_item, package)
            if signal_queue.qsize() > 0:
                # stop signal received
                progress.update(
                    task,
                    description=f"Topic '{topic}' "
                    f"(copied {count} packages ({pretty_size(exported_size)}), stopped",
                    refresh=True,
                )
                return

            pkg_size = len(drift_pkg.blob)
            timestamp = float(drift_pkg.package_id) / 1000
            exported_size += pkg_size
            stats.append((pkg_size, time.time()))
            if len(stats) > 10:
                stats.pop(0)

            if len(stats) > 1:
                speed = sum(s[0] for s in stats) / (stats[-1][1] - stats[0][1])

            yield drift_pkg, task

            count += 1
            progress.update(
                task,
                description=f"Topic '{topic}' "
                f"(copied {count} packages ({pretty_size(exported_size)}), "
                f"speed {pretty_size(speed)}/s)",
                advance=timestamp - last_time,
                refresh=True,
            )

            last_time = timestamp

        progress.update(task, total=1, completed=True)


def filter_topics(topics: List[str], names: List[str]) -> List[str]:
    """Filter entries by names"""
    if not names or len(names) == 0:
        return topics

    if len(names) == 1 and names[0] == "":
        return topics

    def _filter(topic: str) -> bool:
        for name in names:
            if name == topic:
                return True
            if name.endswith("*") and topic.startswith(name[:-1]):
                return True
        return False

    return list(filter(_filter, topics))
