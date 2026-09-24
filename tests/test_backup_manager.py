from netops.backup.manager import ConfigBackupManager
from netops.models.device import Device


def build_device() -> Device:
    return Device(
        name="r1",
        hostname="r1",
        management_ip="10.10.0.11",
        platform="frr",
        role="edge-router",
        site="lab",
        asn=65001,
    )


def test_initial_backup(tmp_path):
    device = build_device()
    manager = ConfigBackupManager(str(tmp_path))

    config = "hostname r1\nrouter bgp 65001"

    result = manager.save(device, config)

    assert result["changed"] is True
    assert result["previous_sha256"] is None

    assert (tmp_path / "r1" / "latest.conf").exists()
    assert (tmp_path / "r1" / "metadata.json").exists()


def test_unchanged_configuration(tmp_path):
    device = build_device()
    manager = ConfigBackupManager(str(tmp_path))

    config = "hostname r1\nrouter bgp 65001"

    first = manager.save(device, config)
    second = manager.save(device, config)

    assert first["changed"] is True
    assert second["changed"] is False
    assert second["previous_sha256"] == second["sha256"]


def test_changed_configuration_creates_previous_backup(tmp_path):
    device = build_device()
    manager = ConfigBackupManager(str(tmp_path))

    original = "hostname r1\nrouter bgp 65001"
    modified = "hostname r1\nrouter bgp 65101"

    manager.save(device, original)
    result = manager.save(device, modified)

    previous_path = tmp_path / "r1" / "previous.conf"
    latest_path = tmp_path / "r1" / "latest.conf"

    assert result["changed"] is True
    assert previous_path.exists()
    assert latest_path.exists()

    assert previous_path.read_text(
        encoding="utf-8"
    ).strip() == original

    assert latest_path.read_text(
        encoding="utf-8"
    ).strip() == modified


def test_changed_configuration_updates_hash(tmp_path):
    device = build_device()
    manager = ConfigBackupManager(str(tmp_path))

    original = "hostname r1"
    modified = "hostname r1\nrouter bgp 65001"

    first = manager.save(device, original)
    second = manager.save(device, modified)

    assert first["sha256"] != second["sha256"]
    assert second["previous_sha256"] == first["sha256"]
