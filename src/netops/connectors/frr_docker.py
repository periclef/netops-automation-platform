import subprocess

from netops.models.device import Device


class FRRDockerConnector:
    def _container_name(self, device: Device) -> str:
        return f"netops-{device.name}"

    def run_command(self, device: Device, command: str) -> str:
        container = self._container_name(device)

        result = subprocess.run(
            [
                "docker",
                "exec",
                container,
                "vtysh",
                "-c",
                command,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Command failed on {device.name}: "
                f"{result.stderr.strip()}"
            )

        return result.stdout.strip()
