from netops.collectors.bgp import collect_bgp_summary, is_bgp_healthy
from netops.collectors.device_info import collect_device_info
from netops.connectors.frr_docker import FRRDockerConnector
from netops.connectors.ssh import SSHConnector
from netops.inventory.loader import load_inventory
from netops.validators.device import validate_device


def main() -> None:
    devices = load_inventory("inventory/devices.yaml")

    reachability = SSHConnector()
    frr_connector = FRRDockerConnector()

    print("NetOps Automation Platform - Device Discovery")
    print("=" * 72)

    reachable_count = 0
    healthy_count = 0
    valid_count = 0

    for device in devices:
        reachable = reachability.is_reachable(device)

        print()
        print(f"Device:       {device.name}")
        print(f"Management:   {device.management_ip}")
        print(f"Platform:     {device.platform}")
        print(f"Role:         {device.role}")
        print(f"Inventory AS: {device.asn}")
        print(f"Reachability: {'UP' if reachable else 'DOWN'}")

        if not reachable:
            print("Operational:  SKIPPED")
            continue

        reachable_count += 1

        try:
            info = collect_device_info(
                device,
                frr_connector,
            )

            bgp = collect_bgp_summary(
                device,
                frr_connector,
            )

            bgp_healthy = is_bgp_healthy(bgp)

            issues = validate_device(
                device,
                info,
                bgp,
            )

            device_valid = not issues

            if bgp_healthy:
                healthy_count += 1

            if device_valid:
                valid_count += 1

            print(f"Hostname:     {info['hostname']}")
            print(f"FRR Version:  {info['version']}")
            print(f"Router ID:    {bgp['router_id']}")
            print(f"Live AS:      {bgp['local_as']}")

            print(
                f"BGP Peers:    "
                f"{bgp['established_peers']}/{bgp['total_peers']}"
            )

            print(
                f"BGP Health:   "
                f"{'HEALTHY' if bgp_healthy else 'UNHEALTHY'}"
            )

            print(
                f"Validation:   "
                f"{'VALID' if device_valid else 'INVALID'}"
            )

            for issue in issues:
                print(f"  Issue:      {issue}")

            for peer in bgp["peers"]:
                print(
                    f"  Peer:       {peer['address']} "
                    f"AS{peer['remote_as']} "
                    f"{peer['state']} "
                    f"RX={peer['prefixes_received']} "
                    f"TX={peer['prefixes_sent']}"
                )

        except Exception as exc:
            print(f"Operational:  ERROR ({exc})")

    print()
    print("Discovery Summary")
    print("=" * 72)
    print(f"Devices:      {len(devices)}")
    print(f"Reachable:    {reachable_count}")
    print(f"Unreachable:  {len(devices) - reachable_count}")
    print(f"BGP Healthy:  {healthy_count}")
    print(f"Valid:        {valid_count}")
    print(f"Invalid:      {reachable_count - valid_count}")


if __name__ == "__main__":
    main()
