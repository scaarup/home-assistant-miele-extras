"""Shared base: one device per Miele appliance, linked to the official device via via_device."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MieleExtrasCoordinator
from .const import DOMAIN, MIELE_DOMAIN


class MieleExtrasEntity(CoordinatorEntity[MieleExtrasCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: MieleExtrasCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        tech = coordinator.data[device_id]["tech_type"]
        # A device belongs to a single integration, so we create our own device and link it to the
        # official one with via_device.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            via_device=(MIELE_DOMAIN, device_id),
            name=f"{tech} Extras",
            manufacturer="Miele",
            model=tech,
            serial_number=device_id,
        )

    @property
    def _services(self) -> dict:
        return self.coordinator.data.get(self._device_id, {}).get("services", {})
