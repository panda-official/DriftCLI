"""Export data from SRC bucket to DST bucket"""
import shutil
import time
from pathlib import Path
from tempfile import gettempdir

import pytest
from drift_client import DriftClient, DriftDataPackage
from drift_protocol.common import (
    DriftPackage,
)


@pytest.fixture(name="topics")
def _make_topics():
    """Make topics"""
    return ["topic1", "topic2"]


@pytest.fixture(name="packages")
def _make_packages():
    """Make packages"""
    packages = []
    for package_id in range(1, 3):
        pkg = DriftPackage()
        pkg.id = package_id
        pkg.status = 0
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
    assert f"Topic '{topics[0]}' (copied 2 packages (4 B)" in result.output
    assert f"Topic '{topics[1]}' (copied 2 packages (4 B)" in result.output

    assert result.exit_code == 0
    assert (export_path / topics[0] / "1.dp").exists()
    assert (export_path / topics[0] / "2.dp").exists()
    assert (export_path / topics[1] / "1.dp").exists()
    assert (export_path / topics[1] / "2.dp").exists()
