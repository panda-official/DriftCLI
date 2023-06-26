"""Export data"""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor, Executor
from pathlib import Path
from typing import List, Tuple

import numpy as np
from drift_client import DriftClient, DriftDataPackage
from drift_protocol.common import StatusCode
from drift_protocol.meta import MetaInfo
from google.protobuf.json_format import MessageToDict
from rich.progress import Progress
from wavelet_buffer import WaveletBuffer
from wavelet_buffer.img import RgbJpeg, HslJpeg, GrayJpeg

from drift_cli.utils.helpers import read_topic, filter_topics


def _export_metadata_to_json(path: Path, pkg: DriftDataPackage):
    with open(f"{path}/{pkg.package_id}.json", "w") as f:
        meta = {
            "id": pkg.package_id,
            "status": pkg.status_code,
            "published_time": pkg.publish_timestamp,
            "source_timestamp": pkg.source_timestamp,
        }
        meta.update(MessageToDict(pkg.meta, preserving_proto_field_name=True))

        json.dump(meta, f, indent=2, sort_keys=False)


def _tokenize(mask: str) -> List[Tuple[str, int]]:
    """turn a channel mask into a list of tokens,
    each with the type as a string, and the absolute channel offset into the buffer
    """
    types = ["RGB", "HSL", "G"]
    tokens = []
    count = 0
    while mask:
        for img_type in types:
            if mask.startswith(img_type):
                tokens.append((img_type, count))
                count += len(img_type)
                mask = mask[len(img_type) :]
                break
    return tokens


def extract_jpeg_images_from_buffer(
    buffer: WaveletBuffer, layout: str, scale_factor: int
) -> List[bytes]:
    """takes a wavelet buffer and returns possibly multiple jpegs"""
    if buffer.parameters.signal_number < len(layout):
        raise RuntimeError(
            f'Wrong channel number in layout "{layout} '
            f"should >= {buffer.parameters.signal_number}"
        )

    scale_factor = min(scale_factor, buffer.parameters.decomposition_steps)

    images = []
    for img_mask, offset in _tokenize(layout):
        ch_slice = buffer[offset : offset + len(img_mask)].compose(
            scale_factor=scale_factor
        )

        if img_mask == "HSL":
            img = HslJpeg().encode(ch_slice)

        elif img_mask == "RGB":
            img = RgbJpeg().encode(ch_slice)

        elif img_mask == "G":
            img = GrayJpeg().encode(ch_slice)

        else:
            raise RuntimeError(f"Wrong channel layout {img_mask} in mask {layout}")

        images.append(img)
    return images


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

        if kwargs.get("with_metadata", False):
            _export_metadata_to_json(Path(dest) / topic, package)


async def _export_jpeg(
    pool: Executor,
    client: DriftClient,
    topic: str,
    dest: str,
    progress: Progress,
    sem,
    **kwargs,
):
    async for package, task in read_topic(pool, client, topic, progress, sem, **kwargs):
        if package.status_code != StatusCode.GOOD:
            progress.console.print(
                f"Can't extract picture from  {topic}/{package.package_id}.dp: {StatusCode.Name(package.status_code)}"
            )
            continue

        meta = package.meta

        if meta.type != MetaInfo.IMAGE:
            progress.update(
                task,
                description=f"[SKIPPED] Topic {topic} is not an image",
                completed=True,
            )
            break

        Path.mkdir(Path(dest) / topic, exist_ok=True, parents=True)
        if package.meta.HasField("image_info"):
            layout = package.meta.image_info.channel_layout
        else:
            layout = "RGB"
        images = extract_jpeg_images_from_buffer(package.as_buffer(), layout, 0)
        for i, img in enumerate(images):
            name = (
                f"{package.package_id}_{i}.jpeg"
                if len(images) > 1
                else f"{package.package_id}.jpeg"
            )
            with open(Path(dest) / topic / name, "wb") as file:
                file.write(img)

        if kwargs.get("with_metadata", False):
            _export_metadata_to_json(Path(dest) / topic, package)


async def _export_csv(
    pool: Executor,
    client: DriftClient,
    topic: str,
    dest: str,
    progress: Progress,
    sem,
    **kwargs,
):
    Path.mkdir(Path(dest), exist_ok=True, parents=True)

    filename = Path(dest) / f"{topic}.csv"
    started = False
    first_timestamp = 0
    last_timestamp = 0
    count = 0
    async for package, task in read_topic(pool, client, topic, progress, sem, **kwargs):
        meta = package.meta
        if meta.type != MetaInfo.TIME_SERIES:
            progress.update(
                task,
                description=f"[SKIPPED] Topic {topic} is not a time series",
                completed=True,
            )
            break

        if not started:
            with open(Path(dest) / f"{topic}.csv", "w") as file:
                file.write(" " * 256 + "\n")
            started = True
            first_timestamp = meta.time_series_info.start_timestamp.ToMilliseconds()
        else:
            if last_timestamp != meta.time_series_info.start_timestamp.ToMilliseconds():
                progress.update(
                    task,
                    description=f"[ERROR] Topic {topic} has gaps",
                    completed=True,
                )
                break

        if package.status_code != 0:
            progress.update(
                task,
                description=f"[ERROR] Topic {topic} has a bad package",
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
                        topic,
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
        topics: Export only these topics, separated by comma. You can use * as a wildcard
        with_meta: Export meta information in JSON format
    """
    sem = asyncio.Semaphore(parallel)
    with Progress() as progress:
        with ThreadPoolExecutor(max_workers=8) as pool:
            topics = filter_topics(client.get_topics(), kwargs.pop("topics", ""))
            task = _export_csv if kwargs.get("csv", False) else _export_topic
            task = _export_jpeg if kwargs.get("jpeg", False) else task

            if kwargs.get("with_metadata", False) and kwargs.get("csv", False):
                RuntimeError("Metadata export is not supported for CSV files")

            tasks = [
                task(
                    pool,
                    client,
                    topic,
                    dest,
                    progress,
                    sem,
                    topics=topics,
                    parallel=parallel // len(topics) + 1,
                    **kwargs,
                )
                for topic in topics
            ]
            await asyncio.gather(*tasks)
