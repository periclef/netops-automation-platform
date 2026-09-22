from netops.models.device import Device


def validate_device(
    device: Device,
    device_info: dict,
    bgp_summary: dict,
) -> list[str]:
    issues = []

    if device.hostname != device_info["hostname"]:
        issues.append(
            f"Hostname mismatch: "
            f"expected={device.hostname} "
            f"actual={device_info['hostname']}"
        )

    if device.asn != bgp_summary["local_as"]:
        issues.append(
            f"ASN mismatch: "
            f"expected={device.asn} "
            f"actual={bgp_summary['local_as']}"
        )

    return issues
