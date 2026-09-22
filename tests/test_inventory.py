from netops.inventory.loader import load_inventory


def test_inventory_loads_all_devices():
    devices = load_inventory("inventory/devices.yaml")

    assert len(devices) == 3


def test_inventory_device_names():
    devices = load_inventory("inventory/devices.yaml")

    names = [device.name for device in devices]

    assert names == ["r1", "r2", "r3"]


def test_inventory_as_numbers():
    devices = load_inventory("inventory/devices.yaml")

    as_numbers = {
        device.name: device.asn
        for device in devices
    }

    assert as_numbers == {
        "r1": 65001,
        "r2": 65002,
        "r3": 65003,
    }


def test_inventory_management_addresses():
    devices = load_inventory("inventory/devices.yaml")

    addresses = {
        device.name: device.management_ip
        for device in devices
    }

    assert addresses == {
        "r1": "10.10.0.11",
        "r2": "10.10.0.12",
        "r3": "10.10.0.13",
    }
