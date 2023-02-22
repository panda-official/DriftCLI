"""Export data"""
import asyncio
from concurrent.futures import ThreadPoolExecutor, Executor
from pathlib import Path

import numpy as np
from drift_client import DriftClient
from drift_protocol.meta import MetaInfo
from rich.progress import Progress

from drift_cli.utils.helpers import read_topic, filter_topics


async def _export_topic(
    pool: Executor,
    client: DriftClient,
    topic: str,
    dest: str,
    progress: Progress,
    sem,
    **kwargs,
):
    async for package, task in read_topic(pool, client, topic, progress, sem, **kwargs):
        Path.mkdir(Path(dest) / topic, exist_ok=True, parents=True)
        with open(Path(dest) / topic / f"{package.package_id}.dp", "wb") as file:
            file.write(package.blob)


async def _export_csv(
    pool: Executor,
    client: DriftClient,
    curren_topic: str,
    dest: str,
    progress: Progress,
    sem,
    **kwargs,
):
    Path.mkdir(Path(dest), exist_ok=True, parents=True)

    filename = Path(dest) / f"{curren_topic}.csv"
    started = False
    first_timestamp = 0
    last_timestamp = 0
    count = 0
    async for package, task in read_topic(
        pool, client, curren_topic, progress, sem, **kwargs
    ):
        meta = package.meta
        if meta.type != MetaInfo.TIME_SERIES:
            progress.update(
                task,
                description=f"[SKIPPED] Topic {curren_topic} is not a time series",
                completed=True,
            )
            break

        if not started:
            with open(Path(dest) / f"{curren_topic}.csv", "w") as file:
                file.write(" " * 256 + "\n")
            started = True
            first_timestamp = meta.time_series_info.start_timestamp.ToMilliseconds()
        else:
            if last_timestamp != meta.time_series_info.start_timestamp.ToMilliseconds():
                progress.update(
                    task,
                    description=f"[ERROR] Topic {curren_topic} has gaps",
                    completed=True,
                )
                break

        if package.status_code != 0:
            progress.update(
                task,
                description=f"[ERROR] Topic {curren_topic} has a bad package",
                completed=True,
            )
            break

        last_timestamp = package.meta.time_series_info.stop_timestamp.ToMilliseconds()
        with open(filename, "a") as file:
            np.savetxt(file, package.as_np(), delimiter=",", fmt="%.5f")

        count += 1

    if started:
        with open(filename, "r+") as file:
            file.seek(0)
            file.write(
                ",".join(
                    [
                        curren_topic,
                        str(count),
                        str(first_timestamp),
                        str(last_timestamp),
                    ]
                )
            )


async def export_raw(client: DriftClient, dest: str, parallel: int, **kwargs):
    """Export data from Drift instance to DST folder
    Args:
        client: Drift client
        dest: Path to a folder
        parallel: Number of parallel tasks
    KArgs:
        start: Export records with timestamps newer than this time point in ISO format
        stop: Export records  with timestamps older than this time point in ISO format
        csv: Export data as CSV instead of raw data
        topics: Export only 5
        hese topics, separated by comma. You can use * as a wildcard
    """
    sem = asyncio.Semaphore(parallel)
    with Progress() as progress:
        with ThreadPoolExecutor() as pool:
            topics = filter_topics(client.get_topics(), kwargs.pop("topics", ""))
            csv = kwargs.pop("csv", False)
            task = _export_csv if csv else _export_topic

            tasks = [
                task(pool, client, topic, dest, progress, sem, topics=topics, **kwargs)
                for topic in topics
            ]
            await asyncio.gather(*tasks)
