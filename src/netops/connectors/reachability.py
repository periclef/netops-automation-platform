import subprocess

from netops.connectors.base import Connector
from netops.models.device import Device


class IcmpReachability(Connector):
    """Check reachability with a single ICMP echo to the management IP."""

    def is_reachable(self, device: Device) -> bool:
        result = subprocess.run(
            [
                "ping",
                "-c",
                "1",
                "-W",
                "1",
                device.management_ip,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        return result.returncode == 0
