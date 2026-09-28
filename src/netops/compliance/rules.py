from netops.compliance.models import CheckResult, DeviceState, Status
from netops.models.device import Device

MISSING = "<missing>"
NONE = "<none>"
ESTABLISHED = "Established"


def _display(value) -> str:
    return MISSING if value is None else str(value)


def _compare(rule: str, expected, actual) -> CheckResult:
    return CheckResult(
        rule=rule,
        status=Status.PASS if expected == actual else Status.FAIL,
        expected=_display(expected),
        actual=_display(actual),
    )


def _peers_by_address(state: DeviceState) -> dict[str, dict]:
    return {
        peer["address"]: peer
        for peer in state.bgp_summary.get("peers", [])
    }


def _peer_label(address: str, remote_as) -> str:
    return f"{address} AS{_display(remote_as)}"


def check_hostname(
    device: Device,
    state: DeviceState,
) -> list[CheckResult]:
    return [
        _compare(
            "Hostname",
            device.hostname,
            state.device_info.get("hostname"),
        )
    ]


def check_local_as(
    device: Device,
    state: DeviceState,
) -> list[CheckResult]:
    return [
        _compare(
            "Local ASN",
            device.asn,
            state.bgp_summary.get("local_as"),
        )
    ]


def check_bgp_peers_configured(
    device: Device,
    state: DeviceState,
) -> list[CheckResult]:
    actual_peers = _peers_by_address(state)
    results = []

    for neighbor in device.bgp_neighbors:
        expected = _peer_label(neighbor.address, neighbor.remote_as)
        peer = actual_peers.get(neighbor.address)

        if peer is None:
            results.append(
                CheckResult(
                    rule="BGP Peer",
                    status=Status.FAIL,
                    expected=expected,
                    actual=MISSING,
                    detail="neighbor is not configured on the device",
                )
            )
            continue

        remote_as = peer.get("remote_as")

        results.append(
            CheckResult(
                rule="BGP Peer",
                status=(
                    Status.PASS
                    if remote_as == neighbor.remote_as
                    else Status.FAIL
                ),
                expected=expected,
                actual=_peer_label(neighbor.address, remote_as),
            )
        )

    return results


def check_bgp_sessions_established(
    device: Device,
    state: DeviceState,
) -> list[CheckResult]:
    actual_peers = _peers_by_address(state)
    results = []

    for neighbor in device.bgp_neighbors:
        peer = actual_peers.get(neighbor.address)

        # A missing peer is already reported by check_bgp_peers_configured.
        if peer is None:
            continue

        session_state = peer.get("state")

        results.append(
            CheckResult(
                rule="BGP Session",
                status=(
                    Status.PASS
                    if session_state == ESTABLISHED
                    else Status.FAIL
                ),
                expected=f"{neighbor.address} {ESTABLISHED}",
                actual=f"{neighbor.address} {_display(session_state)}",
            )
        )

    return results


def check_unexpected_bgp_peers(
    device: Device,
    state: DeviceState,
) -> list[CheckResult]:
    expected_addresses = {
        neighbor.address for neighbor in device.bgp_neighbors
    }

    unexpected = [
        peer
        for peer in state.bgp_summary.get("peers", [])
        if peer["address"] not in expected_addresses
    ]

    if not unexpected:
        return [
            CheckResult(
                rule="Unexpected BGP Peers",
                status=Status.PASS,
                expected=NONE,
                actual=NONE,
            )
        ]

    return [
        CheckResult(
            rule="Unexpected BGP Peers",
            status=Status.FAIL,
            expected=NONE,
            actual=_peer_label(peer["address"], peer.get("remote_as")),
            detail="neighbor is not declared in the inventory",
        )
        for peer in unexpected
    ]
