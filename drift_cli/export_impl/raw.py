"""Export data"""
import asyncio
from concurrent.futures import ThreadPoolExecutor, Executor
from pathlib import Path

from drift_client import DriftClient
from rich.progress import Progress

from drift_cli.utils.helpers import read_topic


async def _export_topic(
    pool: Executor,
    client: DriftClient,
    topic: str,
    dest: str,
    progress: Progress,
    sem,
    **kwargs,
):
    async for package in read_topic(pool, client, topic, progress, sem, **kwargs):
        Path.mkdir(Path(dest) / topic, exist_ok=True, parents=True)
        with open(Path(dest) / topic / f"{package.package_id}.dp", "wb") as file:
            file.write(package.blob)


async def export_raw(client: DriftClient, dest: str, parallel: int, **kwargs):
    """Export data from Drift instance to DST folder
    Args:
        client: Drift client
        dest: Path to a folder
        parallel: Number of parallel tasks
    KArgs:
        start: Export records with timestamps newer than this time point in ISO format
        stop: Export records  with timestamps older than this time point in ISO format
    """
    sem = asyncio.Semaphore(parallel)
    with Progress() as progress:
        with ThreadPoolExecutor() as pool:
            topics = client.get_topics()

            tasks = [
                _export_topic(pool, client, topic, dest, progress, sem, **kwargs)
                for topic in topics
            ]
            await asyncio.gather(*tasks)
