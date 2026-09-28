from dataclasses import dataclass, field


@dataclass
class BgpNeighbor:
    address: str
    remote_as: int


@dataclass
class Device:
    name: str
    hostname: str
    management_ip: str
    platform: str
    role: str
    site: str
    asn: int
    bgp_neighbors: list[BgpNeighbor] = field(default_factory=list)
