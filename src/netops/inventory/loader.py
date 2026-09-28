import ipaddress
from pathlib import Path

import yaml

from netops.models.device import BgpNeighbor, Device


def _load_bgp_neighbors(
    device_name: str,
    raw_neighbors,
) -> list[BgpNeighbor]:
    if raw_neighbors is None:
        return []

    if not isinstance(raw_neighbors, list):
        raise ValueError(
            f"{device_name}: 'bgp_neighbors' must be a list."
        )

    neighbors = []

    for index, entry in enumerate(raw_neighbors):
        if (
            not isinstance(entry, dict)
            or "address" not in entry
            or "remote_as" not in entry
        ):
            raise ValueError(
                f"{device_name}: bgp_neighbors[{index}] must define "
                f"'address' and 'remote_as'."
            )

        try:
            address = str(ipaddress.ip_address(entry["address"]))
        except ValueError as error:
            raise ValueError(
                f"{device_name}: bgp_neighbors[{index}] has an "
                f"invalid address: {entry['address']}"
            ) from error

        remote_as = entry["remote_as"]

        if not isinstance(remote_as, int) or isinstance(remote_as, bool):
            raise ValueError(
                f"{device_name}: bgp_neighbors[{index}] has an "
                f"invalid remote_as: {remote_as}"
            )

        neighbors.append(
            BgpNeighbor(address=address, remote_as=remote_as)
        )

    addresses = [neighbor.address for neighbor in neighbors]
    duplicates = sorted(
        {address for address in addresses if addresses.count(address) > 1}
    )

    if duplicates:
        raise ValueError(
            f"{device_name}: duplicate BGP neighbors: "
            f"{', '.join(duplicates)}"
        )

    return neighbors


def load_inventory(path: str | Path) -> list[Device]:
    inventory_path = Path(path)

    if not inventory_path.exists():
        raise FileNotFoundError(
            f"Inventory file not found: {inventory_path}"
        )

    with inventory_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not data or "devices" not in data:
        raise ValueError(
            "Inventory must contain a 'devices' section."
        )

    devices = []

    for name, attributes in data["devices"].items():
        device = Device(
            name=name,
            hostname=attributes["hostname"],
            management_ip=attributes["management_ip"],
            platform=attributes["platform"],
            role=attributes["role"],
            site=attributes["site"],
            asn=attributes["asn"],
            bgp_neighbors=_load_bgp_neighbors(
                name,
                attributes.get("bgp_neighbors"),
            ),
        )

        devices.append(device)

    return devices
