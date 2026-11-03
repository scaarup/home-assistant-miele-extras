"""Binær sensor: er der firmwareopdatering til apparatet? (RemoteUpdate fra appen)"""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MieleExtrasConfigEntry
from .entity import MieleExtrasEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MieleExtrasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        MieleUpdateAvailable(coordinator, dev_id)
        for dev_id, dev in coordinator.data.items()
        if dev["services"].get("RemoteUpdate", {}).get("available")
    )


class MieleUpdateAvailable(MieleExtrasEntity, BinarySensorEntity):
    _attr_translation_key = "update_available"
    _attr_device_class = BinarySensorDeviceClass.UPDATE

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_update_available"

    @property
    def is_on(self) -> bool | None:
        upd = self._services.get("RemoteUpdate")
        return bool(upd.get("updateAvailable")) if upd else None

    @property
    def extra_state_attributes(self) -> dict[str, bool | None]:
        upd = self._services.get("RemoteUpdate", {})
        return {"update_in_progress": upd.get("updateInProgress")}
