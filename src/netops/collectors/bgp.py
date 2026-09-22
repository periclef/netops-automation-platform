import json

from netops.connectors.frr_docker import FRRDockerConnector
from netops.models.device import Device


def collect_bgp_summary(
    device: Device,
    connector: FRRDockerConnector,
) -> dict:
    output = connector.run_command(
        device,
        "show ip bgp summary json",
    )

    data = json.loads(output)

    if "ipv4Unicast" not in data:
        raise ValueError(
            f"IPv4 BGP information not found for {device.name}"
        )

    bgp = data["ipv4Unicast"]
    peers = bgp.get("peers", {})

    peer_details = []

    for peer_ip, peer in peers.items():
        peer_details.append(
            {
                "address": peer_ip,
                "hostname": peer.get("hostname"),
                "remote_as": peer.get("remoteAs"),
                "state": peer.get("state"),
                "uptime": peer.get("peerUptime"),
                "prefixes_received": peer.get("pfxRcd", 0),
                "prefixes_sent": peer.get("pfxSnt", 0),
            }
        )

    established_peers = sum(
        1
        for peer in peer_details
        if peer["state"] == "Established"
    )

    return {
        "router_id": bgp.get("routerId"),
        "local_as": bgp.get("as"),
        "total_peers": bgp.get("totalPeers", len(peer_details)),
        "established_peers": established_peers,
        "failed_peers": bgp.get("failedPeers", 0),
        "peers": peer_details,
    }


def is_bgp_healthy(summary: dict) -> bool:
    if summary["total_peers"] == 0:
        return False

    return (
        summary["established_peers"]
        == summary["total_peers"]
    )
