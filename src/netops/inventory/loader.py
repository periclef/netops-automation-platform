from pathlib import Path

import yaml

from netops.models.device import Device


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
        )

        devices.append(device)

    return devices
