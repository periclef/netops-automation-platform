from abc import ABC, abstractmethod

from netops.models.device import Device


class Connector(ABC):
    @abstractmethod
    def is_reachable(self, device: Device) -> bool:
        """Return True if the device is reachable."""
        raise NotImplementedError
