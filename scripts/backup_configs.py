from pathlib import Path

from netops.backup.diff import generate_config_diff
from netops.backup.manager import ConfigBackupManager
from netops.collectors.configuration import collect_running_config
from netops.connectors.frr_docker import FRRDockerConnector
from netops.inventory.loader import load_inventory


def main() -> None:
    devices = load_inventory("inventory/devices.yaml")

    connector = FRRDockerConnector()
    backup_manager = ConfigBackupManager()

    print("NetOps Automation Platform - Configuration Backup")
    print("=" * 72)

    changed_count = 0
    unchanged_count = 0
    failed_count = 0

    for device in devices:
        print()
        print(f"Device: {device.name}")

        try:
            config = collect_running_config(
                device,
                connector,
            )

            result = backup_manager.save(
                device,
                config,
            )

            if result["changed"]:
                changed_count += 1

                if result["previous_sha256"] is None:
                    print("Status:  INITIAL BACKUP")
                    print(
                        f"Current:  "
                        f"{result['sha256']}"
                    )

                else:
                    print("Status:  CONFIGURATION CHANGED")
                    print(
                        f"Previous: "
                        f"{result['previous_sha256']}"
                    )
                    print(
                        f"Current:  "
                        f"{result['sha256']}"
                    )

                    previous_path = Path(
                        f"backups/{device.name}/previous.conf"
                    )
                    current_path = Path(
                        f"backups/{device.name}/latest.conf"
                    )

                    if previous_path.exists() and current_path.exists():
                        previous_config = previous_path.read_text(
                            encoding="utf-8"
                        )
                        current_config = current_path.read_text(
                            encoding="utf-8"
                        )

                        diff = generate_config_diff(
                            previous_config,
                            current_config,
                            previous_name=f"{device.name}/previous.conf",
                            current_name=f"{device.name}/latest.conf",
                        )

                        if diff:
                            print()
                            print("Configuration Diff:")
                            print(diff)

            else:
                unchanged_count += 1
                print("Status:  NO CHANGE")
                print(
                    f"SHA256:  "
                    f"{result['sha256']}"
                )

        except Exception as exc:
            failed_count += 1
            print(f"Status:  ERROR ({exc})")

    print()
    print("Backup Summary")
    print("=" * 72)
    print(f"Devices:    {len(devices)}")
    print(f"Changed:    {changed_count}")
    print(f"Unchanged:  {unchanged_count}")
    print(f"Failed:     {failed_count}")


if __name__ == "__main__":
    main()
