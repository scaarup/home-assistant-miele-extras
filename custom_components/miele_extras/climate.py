"""Oven as a thermostat: current and target temperature of the running program, target adjustable."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import MieleExtrasConfigEntry
from .api import MieleApiError, MieleAuthError
from .const import DOMAIN, OVEN_DEVICE_TYPE, OVEN_POLL_SECONDS
from .entity import MieleExtrasEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MieleExtrasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities = []
    for dev_id, dev in coordinator.data.items():
        if dev.get("device_type") == OVEN_DEVICE_TYPE:
            oven = MieleOvenCoordinator(hass, entry, coordinator.api, dev_id)
            await oven.async_refresh()
            entities.append(MieleOvenClimate(coordinator, oven, dev_id))
    async_add_entities(entities)


class MieleOvenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the running program of one oven (cheap, but only that one appliance)."""

    def __init__(self, hass, entry, api, device_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_oven_{device_id}",
            config_entry=entry,
            update_interval=timedelta(seconds=OVEN_POLL_SECONDS),
        )
        self.api = api
        self.device_id = device_id

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_oven_process(self.device_id)
        except MieleAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (MieleApiError, ValueError, KeyError) as err:
            raise UpdateFailed(str(err)) from err


class MieleOvenClimate(MieleExtrasEntity, ClimateEntity):
    _attr_translation_key = "oven"
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_target_temperature_step = 5

    def __init__(self, coordinator, oven: MieleOvenCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._oven = oven
        self._attr_unique_id = f"{device_id}_oven_climate"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._oven.async_add_listener(self.async_write_ha_state))

    @property
    def _proc(self) -> dict[str, Any]:
        return self._oven.data or {}

    @property
    def available(self) -> bool:
        p = self._proc
        return bool(self._oven.last_update_success and p.get("program_id") and p.get("adjustable"))

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        cur, tgt = self.current_temperature, self.target_temperature
        if cur is None or tgt is None:
            return HVACAction.IDLE
        return HVACAction.HEATING if cur < tgt else HVACAction.IDLE

    @property
    def min_temp(self) -> float:
        return self._proc.get("min_c", 30.0)

    @property
    def max_temp(self) -> float:
        return self._proc.get("max_c", 250.0)

    @property
    def current_temperature(self) -> float | None:
        return self._proc.get("current_c") or None

    @property
    def target_temperature(self) -> float | None:
        return self._proc.get("target_c") or None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode != HVACMode.HEAT:
            raise HomeAssistantError("The oven cannot be switched on or off from here, only its temperature changed")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        value = kwargs.get(ATTR_TEMPERATURE)
        proc = self._proc
        if value is None:
            return
        if not (proc.get("program_id") and proc.get("adjustable")):
            raise HomeAssistantError("The oven has no running program with an adjustable temperature")
        try:
            await self._oven.api.async_set_oven_temperature(
                self._device_id, proc["program_id"], value
            )
        except MieleAuthError as err:
            raise HomeAssistantError("Miele login rejected, the token must be replaced") from err
        except MieleApiError as err:
            raise HomeAssistantError(str(err)) from err
        await asyncio.sleep(2)
        await self._oven.async_request_refresh()
