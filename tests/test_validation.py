from netops.models.device import Device
from netops.validators.device import validate_device


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


def test_valid_device():
    device = build_device()

    device_info = {
        "hostname": "r1",
        "version": "8.4_git",
    }

    bgp_summary = {
        "local_as": 65001,
    }

    issues = validate_device(
        device,
        device_info,
        bgp_summary,
    )

    assert issues == []


def test_detects_asn_mismatch():
    device = build_device()

    device_info = {
        "hostname": "r1",
        "version": "8.4_git",
    }

    bgp_summary = {
        "local_as": 65101,
    }

    issues = validate_device(
        device,
        device_info,
        bgp_summary,
    )

    assert len(issues) == 1
    assert issues[0] == (
        "ASN mismatch: expected=65001 actual=65101"
    )


def test_detects_hostname_mismatch():
    device = build_device()

    device_info = {
        "hostname": "WRONG-R1",
        "version": "8.4_git",
    }

    bgp_summary = {
        "local_as": 65001,
    }

    issues = validate_device(
        device,
        device_info,
        bgp_summary,
    )

    assert len(issues) == 1
    assert issues[0] == (
        "Hostname mismatch: expected=r1 actual=WRONG-R1"
    )


def test_detects_multiple_mismatches():
    device = build_device()

    device_info = {
        "hostname": "WRONG-R1",
        "version": "8.4_git",
    }

    bgp_summary = {
        "local_as": 65101,
    }

    issues = validate_device(
        device,
        device_info,
        bgp_summary,
    )

    assert len(issues) == 2
