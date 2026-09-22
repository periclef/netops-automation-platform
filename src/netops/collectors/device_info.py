import re

from netops.connectors.frr_docker import FRRDockerConnector
from netops.models.device import Device


def collect_device_info(
    device: Device,
    connector: FRRDockerConnector,
) -> dict:
    output = connector.run_command(device, "show version")

    first_line = output.splitlines()[0]

    match = re.search(
        r"FRRouting\s+(\S+)\s+\(([^)]+)\)",
        first_line,
    )

    if not match:
        raise ValueError(
            f"Unable to parse FRR version information for {device.name}"
        )

    version = match.group(1)
    hostname = match.group(2)

    return {
        "hostname": hostname,
        "version": version,
    }
