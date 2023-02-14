"""Export data from SRC bucket to DST bucket"""
import shutil
from pathlib import Path
from tempfile import gettempdir

import numpy as np
import pytest
from drift_client import DriftClient, DriftDataPackage
from drift_protocol.common import (
    DriftPackage,
    DataPayload,
)
from drift_protocol.meta import TimeSeriesInfo, MetaInfo
from google.protobuf.any_pb2 import Any  # pylint: disable=no-name-in-module
from wavelet_buffer import WaveletBuffer, WaveletType, denoise


@pytest.fixture(name="topics")
def _make_topics():
    """Make topics"""
    return ["topic1", "topic2"]


@pytest.fixture(name="packages")
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


@pytest.fixture(name="package_names")
def _make_package_names(topics):
    return [[f"{topic}/1.dp", f"{topic}/2.dp"] for topic in topics]


@pytest.fixture(name="client")
def _make_client(mocker, topics, package_names, packages) -> DriftClient:
    kls = mocker.patch("drift_cli.export.DriftClient")
    client = mocker.Mock(spec=DriftClient)
    kls.return_value = client

    client.get_topics.return_value = topics
    client.get_package_names.side_effect = package_names
    client.get_item.side_effect = packages * len(topics)
    return client


@pytest.fixture(name="export_path")
def _make_export_path() -> Path:
    path = Path(gettempdir()) / "drift_export"
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.mark.usefixtures("set_alias", "client")
def test__export_raw_data(runner, conf, export_path, topics):
    """Test export raw data"""
    result = runner(
        f"-c {conf} -p 1 export raw test {export_path} --start 2022-01-01 --stop 2022-01-02"
    )
    assert f"Topic '{topics[0]}' (copied 2 packages (403 B)" in result.output
    assert f"Topic '{topics[1]}' (copied 2 packages (403 B)" in result.output

    assert result.exit_code == 0
    assert (export_path / topics[0] / "1.dp").exists()
    assert (export_path / topics[0] / "2.dp").exists()
    assert (export_path / topics[1] / "1.dp").exists()
    assert (export_path / topics[1] / "2.dp").exists()


@pytest.mark.usefixtures("set_alias", "client")
def test__export_raw_data_as_csv(runner, conf, export_path, topics):
    """Test export raw data as csv"""
    result = runner(
        f"-c {conf} -p 1 export raw test {export_path} --start 2022-01-01 --stop 2022-01-02 --csv"
    )

    assert f"Topic '{topics[0]}' (copied 2 packages (403 B)" in result.output
    assert f"Topic '{topics[1]}' (copied 2 packages (403 B)" in result.output

    assert result.exit_code == 0

    assert (export_path / f"{topics[0]}.csv").exists()
    assert (export_path / f"{topics[1]}.csv").exists()

    with open(export_path / f"{topics[0]}.csv", encoding="utf-8") as file:
        assert file.readline().strip() == "topic1,2,1,3"  # topic, count, start, stop
