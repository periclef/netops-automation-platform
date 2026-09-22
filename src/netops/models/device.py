from dataclasses import dataclass


@dataclass
class Device:
    name: str
    hostname: str
    management_ip: str
    platform: str
    role: str
    site: str
    asn: int
