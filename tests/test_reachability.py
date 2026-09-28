import subprocess

from netops.connectors import reachability
from netops.connectors.reachability import IcmpReachability
from netops.models.device import Device

DEVICE = Device(
    name="r1",
    hostname="r1",
    management_ip="10.10.0.11",
    platform="frr",
    role="edge-router",
    site="lab",
    asn=65001,
)


def fake_run(returncode, calls):
    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, returncode)

    return run


def test_reachable_when_ping_succeeds(monkeypatch):
    calls = []
    monkeypatch.setattr(reachability.subprocess, "run", fake_run(0, calls))

    assert IcmpReachability().is_reachable(DEVICE) is True
    assert calls == [["ping", "-c", "1", "-W", "1", "10.10.0.11"]]


def test_unreachable_when_ping_fails(monkeypatch):
    calls = []
    monkeypatch.setattr(reachability.subprocess, "run", fake_run(1, calls))

    assert IcmpReachability().is_reachable(DEVICE) is False
