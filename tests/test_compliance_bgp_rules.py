import pytest

from netops.compliance.models import DeviceState, Status
from netops.compliance.rules import (
    MISSING,
    NONE,
    check_bgp_peers_configured,
    check_bgp_sessions_established,
    check_unexpected_bgp_peers,
)
from netops.models.device import BgpNeighbor, Device


@pytest.fixture
def r2():
    return Device(
        name="r2",
        hostname="r2",
        management_ip="10.10.0.12",
        platform="frr",
        role="core-router",
        site="lab",
        asn=65002,
        bgp_neighbors=[
            BgpNeighbor(address="10.0.12.2", remote_as=65001),
            BgpNeighbor(address="10.0.23.3", remote_as=65003),
        ],
    )


def peer(address, remote_as, state="Established"):
    return {"address": address, "remote_as": remote_as, "state": state}


def make_state(*peers):
    return DeviceState(
        device_info={"hostname": "r2"},
        bgp_summary={"local_as": 65002, "peers": list(peers)},
    )


HEALTHY = make_state(
    peer("10.0.12.2", 65001),
    peer("10.0.23.3", 65003),
)


def test_peers_configured_pass(r2):
    results = check_bgp_peers_configured(r2, HEALTHY)

    assert [r.status for r in results] == [Status.PASS, Status.PASS]
    assert results[0].expected == "10.0.12.2 AS65001"
    assert results[0].actual == "10.0.12.2 AS65001"


def test_missing_peer_fails(r2):
    state = make_state(peer("10.0.12.2", 65001))

    results = check_bgp_peers_configured(r2, state)

    assert results[1].status is Status.FAIL
    assert results[1].expected == "10.0.23.3 AS65003"
    assert results[1].actual == MISSING


def test_wrong_remote_as_fails(r2):
    state = make_state(
        peer("10.0.12.2", 65001),
        peer("10.0.23.3", 65099, state="Active"),
    )

    results = check_bgp_peers_configured(r2, state)

    assert results[1].status is Status.FAIL
    assert results[1].actual == "10.0.23.3 AS65099"


def test_sessions_established_pass(r2):
    results = check_bgp_sessions_established(r2, HEALTHY)

    assert [r.status for r in results] == [Status.PASS, Status.PASS]


def test_session_not_established_fails(r2):
    state = make_state(
        peer("10.0.12.2", 65001),
        peer("10.0.23.3", 65003, state="Active"),
    )

    results = check_bgp_sessions_established(r2, state)

    assert results[1].status is Status.FAIL
    assert results[1].actual == "10.0.23.3 Active"


def test_session_check_skips_missing_peer(r2):
    state = make_state(peer("10.0.12.2", 65001))

    results = check_bgp_sessions_established(r2, state)

    assert len(results) == 1
    assert results[0].expected == "10.0.12.2 Established"


def test_no_unexpected_peers_pass(r2):
    [result] = check_unexpected_bgp_peers(r2, HEALTHY)

    assert result.status is Status.PASS
    assert result.actual == NONE


def test_unexpected_peer_fails(r2):
    state = make_state(
        peer("10.0.12.2", 65001),
        peer("10.0.23.3", 65003),
        peer("10.0.99.1", 65099),
    )

    [result] = check_unexpected_bgp_peers(r2, state)

    assert result.status is Status.FAIL
    assert result.actual == "10.0.99.1 AS65099"


def test_summary_without_peers(r2):
    state = DeviceState(device_info={}, bgp_summary={})

    configured = check_bgp_peers_configured(r2, state)
    [unexpected] = check_unexpected_bgp_peers(r2, state)

    assert all(r.status is Status.FAIL for r in configured)
    assert unexpected.status is Status.PASS
