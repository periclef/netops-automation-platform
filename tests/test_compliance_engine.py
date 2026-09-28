from netops.compliance.engine import error_report, evaluate_device
from netops.compliance.models import CheckResult, DeviceState, Status
from netops.compliance.report import format_report
from netops.models.device import BgpNeighbor, Device

DEVICE = Device(
    name="r1",
    hostname="r1",
    management_ip="10.10.0.11",
    platform="frr",
    role="edge-router",
    site="lab",
    asn=65001,
    bgp_neighbors=[BgpNeighbor(address="10.0.12.3", remote_as=65002)],
)

HEALTHY_STATE = DeviceState(
    device_info={"hostname": "r1", "version": "8.4_git"},
    bgp_summary={
        "local_as": 65001,
        "peers": [
            {
                "address": "10.0.12.3",
                "remote_as": 65002,
                "state": "Established",
            }
        ],
    },
)


def test_evaluate_healthy_device_is_compliant():
    report = evaluate_device(DEVICE, HEALTHY_STATE)

    assert report.status is Status.PASS
    assert [r.rule for r in report.results] == [
        "Hostname",
        "Local ASN",
        "BGP Peer",
        "BGP Session",
        "Unexpected BGP Peers",
    ]


def test_rule_exception_becomes_fail_and_other_rules_run():
    def broken_rule(device, state):
        raise KeyError("peers")

    def ok_rule(device, state):
        return [CheckResult("OK", Status.PASS, "x", "x")]

    report = evaluate_device(DEVICE, HEALTHY_STATE, rules=[broken_rule, ok_rule])

    assert report.status is Status.FAIL
    assert report.results[0].rule == "broken_rule"
    assert "KeyError" in report.results[0].detail
    assert report.results[1].status is Status.PASS


def test_error_report_is_fail():
    report = error_report(DEVICE, "Reachability", "UP", "DOWN")

    assert report.status is Status.FAIL
    assert report.results[0].rule == "Reachability"


def test_format_report():
    report = evaluate_device(DEVICE, HEALTHY_STATE)

    text = format_report(report)

    assert text.startswith("Device: r1")
    assert "[PASS] BGP Peer\n       expected=10.0.12.3 AS65002" in text
    assert text.endswith("Compliance: PASS")


def test_format_report_includes_detail():
    report = error_report(DEVICE, "Reachability", "UP", "DOWN", detail="timeout")

    text = format_report(report)

    assert "[FAIL] Reachability" in text
    assert "detail=timeout" in text
    assert text.endswith("Compliance: FAIL")
