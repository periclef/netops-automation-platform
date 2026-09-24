import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from netops.collectors.configuration import calculate_config_hash
from netops.models.device import Device


class ConfigBackupManager:
    def __init__(self, backup_root: str = "backups") -> None:
        self.backup_root = Path(backup_root)

    def _device_directory(self, device: Device) -> Path:
        return self.backup_root / device.name

    def _config_path(self, device: Device) -> Path:
        return self._device_directory(device) / "latest.conf"

    def _previous_config_path(self, device: Device) -> Path:
        return self._device_directory(device) / "previous.conf"

    def _metadata_path(self, device: Device) -> Path:
        return self._device_directory(device) / "metadata.json"

    def _load_metadata(self, device: Device) -> dict | None:
        metadata_path = self._metadata_path(device)

        if not metadata_path.exists():
            return None

        with metadata_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save(self, device: Device, config: str) -> dict:
        device_directory = self._device_directory(device)
        device_directory.mkdir(parents=True, exist_ok=True)

        config_path = self._config_path(device)
        previous_config_path = self._previous_config_path(device)
        metadata_path = self._metadata_path(device)

        current_hash = calculate_config_hash(config)
        previous_metadata = self._load_metadata(device)

        previous_hash = None

        if previous_metadata:
            previous_hash = previous_metadata.get("sha256")

        changed = previous_hash != current_hash

        if changed:
            if config_path.exists():
                shutil.copy2(
                    config_path,
                    previous_config_path,
                )

            config_path.write_text(
                config + "\n",
                encoding="utf-8",
            )

        metadata = {
            "device": device.name,
            "hostname": device.hostname,
            "management_ip": device.management_ip,
            "platform": device.platform,
            "sha256": current_hash,
            "previous_sha256": previous_hash,
            "changed": changed,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(
                metadata,
                file,
                indent=2,
            )
            file.write("\n")

        return metadata
