from dataclasses import dataclass, field
from enum import StrEnum


class Status(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class DeviceState:
    device_info: dict
    bgp_summary: dict


@dataclass
class CheckResult:
    rule: str
    status: Status
    expected: str
    actual: str
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.status is Status.PASS


@dataclass
class DeviceComplianceReport:
    device: str
    results: list[CheckResult] = field(default_factory=list)

    @property
    def failed(self) -> list[CheckResult]:
        return [result for result in self.results if not result.passed]

    @property
    def status(self) -> Status:
        if self.results and not self.failed:
            return Status.PASS

        return Status.FAIL
