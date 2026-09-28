from netops.compliance.models import DeviceComplianceReport

INDENT = " " * 7


def format_report(report: DeviceComplianceReport) -> str:
    lines = [f"Device: {report.device}", ""]

    for result in report.results:
        lines.append(f"[{result.status}] {result.rule}")
        lines.append(f"{INDENT}expected={result.expected}")
        lines.append(f"{INDENT}actual={result.actual}")

        if result.detail:
            lines.append(f"{INDENT}detail={result.detail}")

        lines.append("")

    lines.append(f"Compliance: {report.status}")

    return "\n".join(lines)
