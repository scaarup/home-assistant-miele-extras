"""Sensors for Miele CareStatus (maintenance, e.g. a dishwasher's seal and door)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MieleExtrasConfigEntry
from .climate import MieleOvenCoordinator, async_get_oven_coordinator
from .const import OVEN_DEVICE_TYPE
from .entity import MieleExtrasEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MieleExtrasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities = []
    for dev_id, dev in coordinator.data.items():
        care = dev["services"].get("CareStatus", {})
        if care.get("available"):
            for comp in care.get("components", []):
                entities.append(MieleCareStatus(coordinator, dev_id, comp["component"]))
        if dev.get("device_type") == OVEN_DEVICE_TYPE:
            oven = await async_get_oven_coordinator(hass, entry, coordinator, dev_id)
            entities.append(MieleOvenRemainingTime(coordinator, oven, dev_id))
    async_add_entities(entities)


class MieleCareStatus(MieleExtrasEntity, SensorEntity):
    _attr_translation_key = "care_status"

    def __init__(self, coordinator, device_id: str, component: str) -> None:
        super().__init__(coordinator, device_id)
        self._component = component
        self._attr_unique_id = f"{device_id}_care_{component.lower()}"
        self._attr_translation_placeholders = {"component": component.replace("_", " ").lower()}

    def _comp(self) -> dict[str, Any]:
        for c in self._services.get("CareStatus", {}).get("components", []):
            if c.get("component") == self._component:
                return c
        return {}

    @property
    def native_value(self) -> str | None:
        status = self._comp().get("status")
        return status.lower() if status else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        info = self._comp().get("careIntervalInfo") or {}
        return {
            "interval_type": self._comp().get("careIntervalType"),
            "last_care_at": info.get("lastCareAt"),
            "next_care_required_at": info.get("nextCareRequiredAt"),
        }


class MieleOvenRemainingTime(MieleExtrasEntity, SensorEntity):
    """Remaining time of the running oven program, as shown in the Miele app."""

    _attr_translation_key = "oven_remaining_time"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator, oven: MieleOvenCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._oven = oven
        self._attr_unique_id = f"{device_id}_oven_remaining_time"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._oven.async_add_listener(self.async_write_ha_state))

    @property
    def available(self) -> bool:
        return self._oven.last_update_success

    @property
    def native_value(self) -> int | None:
        return (self._oven.data or {}).get("remaining_s")
