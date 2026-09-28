import argparse
import sys

from netops.collectors.bgp import collect_bgp_summary
from netops.collectors.device_info import collect_device_info
from netops.compliance.engine import error_report, evaluate_device
from netops.compliance.models import DeviceState, Status
from netops.compliance.report import format_report
from netops.connectors.frr_docker import FRRDockerConnector
from netops.connectors.ssh import SSHConnector
from netops.inventory.loader import load_inventory

EXIT_COMPLIANT = 0
EXIT_NON_COMPLIANT = 1
EXIT_ERROR = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check live devices against the inventory intent.",
    )
    parser.add_argument(
        "--inventory",
        default="inventory/devices.yaml",
        help="path to the inventory file",
    )
    parser.add_argument(
        "--device",
        action="append",
        help="limit the check to a device (repeatable)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        devices = load_inventory(args.inventory)
    except (OSError, ValueError) as exc:
        print(f"Inventory error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.device:
        unknown = set(args.device) - {device.name for device in devices}

        if unknown:
            print(
                f"Unknown device(s): {', '.join(sorted(unknown))}",
                file=sys.stderr,
            )
            return EXIT_ERROR

        devices = [
            device for device in devices if device.name in args.device
        ]

    reachability = SSHConnector()
    frr_connector = FRRDockerConnector()

    print("NetOps Automation Platform - Configuration Compliance")
    print("=" * 72)

    reports = []

    for device in devices:
        if not reachability.is_reachable(device):
            report = error_report(
                device,
                rule="Reachability",
                expected=f"{device.management_ip} UP",
                actual=f"{device.management_ip} DOWN",
                detail="live state not collected",
            )
        else:
            try:
                state = DeviceState(
                    device_info=collect_device_info(device, frr_connector),
                    bgp_summary=collect_bgp_summary(device, frr_connector),
                )
                report = evaluate_device(device, state)
            except Exception as exc:
                report = error_report(
                    device,
                    rule="State Collection",
                    expected="device state collected",
                    actual="collection failed",
                    detail=str(exc),
                )

        reports.append(report)

        print()
        print(format_report(report))

    compliant = sum(
        1 for report in reports if report.status is Status.PASS
    )

    print()
    print("Compliance Summary")
    print("=" * 72)
    print(f"Devices:        {len(reports)}")
    print(f"Compliant:      {compliant}")
    print(f"Non-compliant:  {len(reports) - compliant}")

    if compliant == len(reports):
        return EXIT_COMPLIANT

    return EXIT_NON_COMPLIANT


if __name__ == "__main__":
    sys.exit(main())
