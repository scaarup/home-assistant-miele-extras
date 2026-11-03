"""Sensorer for Mieles CareStatus (vedligehold, fx opvaskemaskinens pakning og dør)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    entities = []
    for dev_id, dev in coordinator.data.items():
        care = dev["services"].get("CareStatus", {})
        if care.get("available"):
            for comp in care.get("components", []):
                entities.append(MieleCareStatus(coordinator, dev_id, comp["component"]))
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
