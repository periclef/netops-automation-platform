import pytest

from netops.inventory.loader import load_inventory
from netops.models.device import BgpNeighbor


DEVICE_HEADER = """devices:
  r1:
    hostname: r1
    management_ip: 10.10.0.11
    platform: frr
    role: edge-router
    site: lab
    asn: 65001
"""


def write_inventory(tmp_path, neighbors_yaml: str = ""):
    path = tmp_path / "devices.yaml"
    path.write_text(DEVICE_HEADER + neighbors_yaml, encoding="utf-8")
    return path


def test_loads_bgp_neighbors(tmp_path):
    path = write_inventory(
        tmp_path,
        "    bgp_neighbors:\n"
        "      - address: 10.0.12.3\n"
        "        remote_as: 65002\n",
    )

    device = load_inventory(path)[0]

    assert device.bgp_neighbors == [
        BgpNeighbor(address="10.0.12.3", remote_as=65002)
    ]


def test_missing_bgp_neighbors_defaults_to_empty_list(tmp_path):
    path = write_inventory(tmp_path)

    device = load_inventory(path)[0]

    assert device.bgp_neighbors == []


def test_bgp_neighbors_must_be_list(tmp_path):
    path = write_inventory(
        tmp_path,
        "    bgp_neighbors: 10.0.12.3\n",
    )

    with pytest.raises(ValueError, match="must be a list"):
        load_inventory(path)


def test_neighbor_missing_remote_as(tmp_path):
    path = write_inventory(
        tmp_path,
        "    bgp_neighbors:\n"
        "      - address: 10.0.12.3\n",
    )

    with pytest.raises(ValueError, match=r"bgp_neighbors\[0\] must define"):
        load_inventory(path)


def test_neighbor_invalid_address(tmp_path):
    path = write_inventory(
        tmp_path,
        "    bgp_neighbors:\n"
        "      - address: 10.0.12.300\n"
        "        remote_as: 65002\n",
    )

    with pytest.raises(ValueError, match="invalid address"):
        load_inventory(path)


@pytest.mark.parametrize("remote_as", ['"65002"', "true"])
def test_neighbor_invalid_remote_as(tmp_path, remote_as):
    path = write_inventory(
        tmp_path,
        "    bgp_neighbors:\n"
        "      - address: 10.0.12.3\n"
        f"        remote_as: {remote_as}\n",
    )

    with pytest.raises(ValueError, match="invalid remote_as"):
        load_inventory(path)


def test_duplicate_neighbors(tmp_path):
    path = write_inventory(
        tmp_path,
        "    bgp_neighbors:\n"
        "      - address: 10.0.12.3\n"
        "        remote_as: 65002\n"
        "      - address: 10.0.12.3\n"
        "        remote_as: 65002\n",
    )

    with pytest.raises(ValueError, match="duplicate BGP neighbors: 10.0.12.3"):
        load_inventory(path)
