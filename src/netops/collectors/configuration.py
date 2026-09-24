import hashlib

from netops.connectors.frr_docker import FRRDockerConnector
from netops.models.device import Device


def collect_running_config(
    device: Device,
    connector: FRRDockerConnector,
) -> str:
    """Collect the running configuration from a device."""

    config = connector.run_command(
        device,
        "show running-config",
    )

    if not config:
        raise ValueError(
            f"Empty running configuration received from {device.name}"
        )

    return config


def calculate_config_hash(config: str) -> str:
    """Return a SHA-256 hash for a configuration."""

    return hashlib.sha256(
        config.encode("utf-8")
    ).hexdigest()
