"""Miele Extras: features from the Miele app API that the official integration lacks."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MieleApiError, MieleAuthError, MieleExtrasApi
from .const import CONF_REFRESH_TOKEN, DOMAIN, UPDATE_INTERVAL_MIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["camera", "binary_sensor", "sensor"]


class MieleExtrasCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetches the appliance list and services ({serial: {"tech_type", "services"}})."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: MieleExtrasApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MIN),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.api.async_get_devices()
            data: dict[str, dict[str, Any]] = {}
            for dev_id, info in devices.items():
                data[dev_id] = {**info, "services": await self.api.async_get_services(dev_id)}
            return data
        except MieleAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except MieleApiError as err:
            raise UpdateFailed(str(err)) from err


type MieleExtrasConfigEntry = ConfigEntry[MieleExtrasCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: MieleExtrasConfigEntry) -> bool:
    def _store_token(token: str) -> None:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_REFRESH_TOKEN: token}
        )

    api = MieleExtrasApi(
        async_get_clientsession(hass), entry.data[CONF_REFRESH_TOKEN], _store_token
    )
    coordinator = MieleExtrasCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MieleExtrasConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
