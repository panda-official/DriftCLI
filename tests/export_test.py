"""Export data from SRC bucket to DST bucket"""
# pylint: disable=too-many-arguments
import shutil
from pathlib import Path
from tempfile import gettempdir
from typing import List

import numpy as np
import pytest
from drift_client import DriftClient, DriftDataPackage
from drift_protocol.common import (
    DriftPackage,
    DataPayload,
    StatusCode,
)
from drift_protocol.meta import TimeSeriesInfo, MetaInfo, ImageInfo
from google.protobuf.any_pb2 import Any  # pylint: disable=no-name-in-module
from wavelet_buffer import WaveletBuffer, WaveletType, denoise
from wavelet_buffer.img import WaveletImage, codecs


@pytest.fixture(name="topics")
def _make_topics():
    """Make topics"""
    return ["topic1", "topic2"]


@pytest.fixture(name="timeseries")
def _make_packages():
    """Make packages"""
    packages = []
    signal = np.array(
        [0.1, 0.2, 0.5, 0.1, 0.2, 0.1, 0.6, 0.1, 0.1, 0.2], dtype=np.float32
    )

    buffer = WaveletBuffer(
        signal_shape=[len(signal)],
        signal_number=1,
        decomposition_steps=2,
        wavelet_type=WaveletType.DB1,
    )
    buffer.decompose(signal, denoise.Null())

    # Prepare payload
    payload = DataPayload()
    payload.data = buffer.serialize(compression_level=16)

    msg = Any()
    msg.Pack(payload)

    for package_id in range(1, 3):
        pkg = DriftPackage()
        pkg.id = package_id
        pkg.status = 0
        pkg.data.append(msg)

        info = TimeSeriesInfo()
        info.start_timestamp.FromMilliseconds(package_id)
        info.stop_timestamp.FromMilliseconds(package_id + 1)

        pkg.meta.type = MetaInfo.TIME_SERIES
        pkg.meta.time_series_info.CopyFrom(info)

        packages.append(DriftDataPackage(pkg.SerializeToString()))
    return packages


@pytest.fixture(name="image_pkgs")
def _make_image_pkgs() -> List[DriftPackage]:
    packages = []
    image = np.zeros((3, 100, 100), dtype=np.float32)
    buffer = WaveletBuffer(
        signal_shape=[100, 100],
        signal_number=3,
        decomposition_steps=2,
        wavelet_type=WaveletType.DB1,
    )
    buffer.decompose(image, denoise.Null())
    for package_id in range(1, 3):
        pkg = DriftPackage()
        pkg.id = package_id
        pkg.status = 0

        payload = DataPayload()
        payload.data = buffer.serialize(compression_level=0)

        msg = Any()
        msg.Pack(payload)
        pkg.data.append(msg)

        info = ImageInfo()
        info.type = ImageInfo.WB
        info.width = 100
        info.height = 100
        info.channel_layout = "RGB"

        pkg.meta.type = MetaInfo.IMAGE
        pkg.meta.image_info.CopyFrom(info)

        packages.append(pkg)
    return packages


@pytest.fixture(name="images")
def _make_images(image_pkgs) -> list[DriftDataPackage]:
    return [DriftDataPackage(pkg.SerializeToString()) for pkg in image_pkgs]


@pytest.fixture(name="package_names")
def _make_package_names(topics):
    return [[f"{topic}/1.dp", f"{topic}/2.dp"] for topic in topics]


@pytest.fixture(name="client")
def _make_client(mocker, topics, package_names) -> DriftClient:
    kls = mocker.patch("drift_cli.export.DriftClient")
    client = mocker.Mock(spec=DriftClient)
    kls.return_value = client

    client.get_topics.return_value = topics
    client.get_package_names.side_effect = package_names
    return client


@pytest.fixture(name="export_path")
def _make_export_path() -> Path:
    path = Path(gettempdir()) / "drift_export"
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.mark.usefixtures("set_alias")
def test__export_raw_data(runner, client, conf, export_path, topics, timeseries):
    """Test export raw data"""
    client.get_item.side_effect = timeseries * len(topics)
    result = runner(
        f"-c {conf} -p 2 export raw test {export_path} --start 2022-01-01 --stop 2022-01-02"
    )
    assert f"Topic '{topics[0]}' (copied 2 packages (943 B)" in result.output
    assert f"Topic '{topics[1]}' (copied 2 packages (943 B)" in result.output

    assert result.exit_code == 0
    assert (export_path / topics[0] / "1.dp").exists()
    assert (export_path / topics[0] / "2.dp").exists()
    assert (export_path / topics[1] / "1.dp").exists()
    assert (export_path / topics[1] / "2.dp").exists()


@pytest.mark.usefixtures("set_alias")
def test__export_raw_data_as_csv(runner, client, conf, export_path, topics, timeseries):
    """Test export raw data as csv"""
    client.get_item.side_effect = timeseries * len(topics)
    result = runner(
        f"-c {conf} -p 2 export raw test {export_path} --start 2022-01-01 --stop 2022-01-02 --csv"
    )

    assert f"Topic '{topics[0]}' (copied 2 packages (943 B)" in result.output
    assert f"Topic '{topics[1]}' (copied 2 packages (943 B)" in result.output

    assert result.exit_code == 0

    assert (export_path / f"{topics[0]}.csv").exists()
    assert (export_path / f"{topics[1]}.csv").exists()

    with open(export_path / f"{topics[0]}.csv", encoding="utf-8") as file:
        assert file.readline().strip() == "topic1,2,1,3"  # topic, count, start, stop


@pytest.mark.usefixtures("set_alias", "client")
def test__export_raw_data_start_stop_required(runner, conf, export_path):
    """Test export raw data start stop required"""
    result = runner(f"-c {conf} -p 1 export raw test {export_path}")
    assert "Error: --start and --stop are required" in result.output
    assert result.exit_code == 1


@pytest.mark.usefixtures("set_alias")
def test__export_raw_data_no_timeseries(runner, client, conf, export_path):
    """Should skip no timeseries"""
    pkg = DriftPackage()
    pkg.meta.type = MetaInfo.IMAGE
    client.get_item.side_effect = [DriftDataPackage(pkg.SerializeToString())] * 2

    result = runner(
        f"-c {conf} -p 1 export raw test {export_path} --start 2022-01-01 --stop 2022-01-02 --csv"
    )
    assert "[SKIPPED] Topic topic1 is not a time series" in result.output


@pytest.mark.usefixtures("set_alias")
def test__export_raw_data_topics(runner, client, conf, export_path, topics, timeseries):
    """Should export only selected topics"""
    client.get_item.side_effect = timeseries * len(topics)
    result = runner(
        f"-c {conf} -p 1 export raw test {export_path} --start 2022-01-01 --stop 2022-01-02 "
        f"--topics {topics[0]}"
    )

    assert f"'{topics[1]}'" not in result.output
    assert result.exit_code == 0

    assert (export_path / topics[0] / "1.dp").exists()
    assert (export_path / topics[0] / "2.dp").exists()
    assert not (export_path / topics[1] / "1.dp").exists()
    assert not (export_path / topics[1] / "2.dp").exists()


@pytest.mark.usefixtures("set_alias")
def test__export_raw_data_topics_jpeg(
    runner, client, conf, export_path, topics, images
):
    """Should exctract jpeg from wavelet buffers"""
    client.get_item.side_effect = images * len(topics)
    result = runner(
        f"-c {conf} -p 1 export raw test {export_path} --start 2022-01-01 --stop 2022-01-02 "
        f"--jpeg"
    )

    assert f"Topic '{topics[0]}' (copied 2 packages (241 KB)" in result.output
    assert result.exit_code == 0

    img = WaveletImage([100, 100], 3, 1, WaveletType.DB1)
    img.import_from_file(
        str(export_path / topics[0] / "1.jpeg"), denoise.Null(), codecs.RgbJpeg()
    )
    img.import_from_file(
        str(export_path / topics[1] / "2.jpeg"), denoise.Null(), codecs.RgbJpeg()
    )


@pytest.mark.usefixtures("set_alias")
def test__export_raw_jpeg_skip_bad_packages(runner, client, conf, export_path, topics):
    """Should skip bad packages and continue"""
    bad_package = DriftPackage()
    bad_package.id = 1
    bad_package.status = StatusCode.BAD

    client.get_item.side_effect = (
        [DriftDataPackage(bad_package.SerializeToString())] * 2 * len(topics)
    )
    result = runner(
        f"-c {conf} -p 1 export raw test {export_path} --start 2022-01-01 --stop 2022-01-02 "
        f"--jpeg"
    )

    assert "Can't extract picture from  topic1/1.dp" in result.output
    assert "Can't extract picture from  topic2/1.dp" in result.output
    assert result.exit_code == 0

    assert not (export_path / topics[0] / "1.jpeg").exists()
    assert not (export_path / topics[1] / "1.jpeg").exists()


@pytest.mark.usefixtures("set_alias")
def test__export_raw_jpeg_stacked_image(
    runner, client, conf, export_path, topics, image_pkgs
):
    """Should export stacked image as few jpeg files"""
    for pkg in image_pkgs:
        pkg.meta.image_info.channel_layout = "GGG"

    images = [DriftDataPackage(pkg.SerializeToString()) for pkg in image_pkgs]
    client.get_item.side_effect = images * len(topics)
    result = runner(
        f"-c {conf} -p 1 export raw test {export_path} --start 2022-01-01 --stop 2022-01-02 "
        f"--jpeg"
    )

    assert f"Topic '{topics[0]}' (copied 2 packages (241 KB)" in result.output

    img = WaveletImage([100, 100], 3, 1, WaveletType.DB1)
    img.import_from_file(
        str(export_path / topics[0] / "1_0.jpeg"), denoise.Null(), codecs.GrayJpeg()
    )
    img.import_from_file(
        str(export_path / topics[0] / "1_1.jpeg"), denoise.Null(), codecs.GrayJpeg()
    )
    img.import_from_file(
        str(export_path / topics[0] / "1_2.jpeg"), denoise.Null(), codecs.GrayJpeg()
    )
