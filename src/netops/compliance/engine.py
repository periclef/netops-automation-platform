from collections.abc import Callable, Sequence

from netops.compliance.models import (
    CheckResult,
    DeviceComplianceReport,
    DeviceState,
    Status,
)
from netops.compliance.rules import (
    check_bgp_peers_configured,
    check_bgp_sessions_established,
    check_hostname,
    check_local_as,
    check_unexpected_bgp_peers,
)
from netops.models.device import Device

Rule = Callable[[Device, DeviceState], list[CheckResult]]

DEFAULT_RULES: tuple[Rule, ...] = (
    check_hostname,
    check_local_as,
    check_bgp_peers_configured,
    check_bgp_sessions_established,
    check_unexpected_bgp_peers,
)


def evaluate_device(
    device: Device,
    state: DeviceState,
    rules: Sequence[Rule] = DEFAULT_RULES,
) -> DeviceComplianceReport:
    report = DeviceComplianceReport(device=device.name)

    for rule in rules:
        try:
            report.results.extend(rule(device, state))
        except Exception as exc:
            # A broken rule must not hide the results of the other rules.
            report.results.append(
                CheckResult(
                    rule=rule.__name__,
                    status=Status.FAIL,
                    expected="rule executed",
                    actual="rule error",
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )

    return report


def error_report(
    device: Device,
    rule: str,
    expected: str,
    actual: str,
    detail: str = "",
) -> DeviceComplianceReport:
    return DeviceComplianceReport(
        device=device.name,
        results=[
            CheckResult(
                rule=rule,
                status=Status.FAIL,
                expected=expected,
                actual=actual,
                detail=detail,
            )
        ],
    )
