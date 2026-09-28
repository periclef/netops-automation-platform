import pytest

from netops.compliance.models import (
    CheckResult,
    DeviceComplianceReport,
    DeviceState,
    Status,
)
from netops.compliance.rules import MISSING, check_hostname, check_local_as
from netops.models.device import Device


@pytest.fixture
def device():
    return Device(
        name="r1",
        hostname="r1",
        management_ip="10.10.0.11",
        platform="frr",
        role="edge-router",
        site="lab",
        asn=65001,
    )


def make_state(hostname="r1", local_as=65001):
    return DeviceState(
        device_info={"hostname": hostname},
        bgp_summary={"local_as": local_as},
    )


def test_hostname_pass(device):
    [result] = check_hostname(device, make_state())

    assert result.status is Status.PASS
    assert result.expected == "r1"
    assert result.actual == "r1"


def test_hostname_fail(device):
    [result] = check_hostname(device, make_state(hostname="r1-old"))

    assert result.status is Status.FAIL
    assert result.actual == "r1-old"


def test_hostname_missing(device):
    state = DeviceState(device_info={}, bgp_summary={})

    [result] = check_hostname(device, state)

    assert result.status is Status.FAIL
    assert result.actual == MISSING


def test_local_as_pass(device):
    [result] = check_local_as(device, make_state())

    assert result.status is Status.PASS
    assert result.expected == "65001"


def test_local_as_fail(device):
    [result] = check_local_as(device, make_state(local_as=65101))

    assert result.status is Status.FAIL
    assert result.actual == "65101"


def test_local_as_type_mismatch_is_fail(device):
    [result] = check_local_as(device, make_state(local_as="65001"))

    assert result.status is Status.FAIL


def test_report_pass_when_all_checks_pass():
    report = DeviceComplianceReport(
        device="r1",
        results=[CheckResult("Hostname", Status.PASS, "r1", "r1")],
    )

    assert report.status is Status.PASS
    assert report.failed == []


def test_report_fail_when_any_check_fails():
    report = DeviceComplianceReport(
        device="r1",
        results=[
            CheckResult("Hostname", Status.PASS, "r1", "r1"),
            CheckResult("Local ASN", Status.FAIL, "65001", "65101"),
        ],
    )

    assert report.status is Status.FAIL
    assert len(report.failed) == 1


def test_empty_report_is_fail():
    report = DeviceComplianceReport(device="r1")

    assert report.status is Status.FAIL
