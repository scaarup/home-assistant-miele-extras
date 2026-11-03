"""Kamera for apparater, hvor appen har en aktiv kamera-service (fx ovnen)."""
from __future__ import annotations

import logging
import time

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MieleExtrasConfigEntry
from .api import MieleApiError, MieleAuthError
from .const import MIN_IMAGE_INTERVAL
from .entity import MieleExtrasEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MieleExtrasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        MieleExtrasCamera(coordinator, dev_id)
        for dev_id, dev in coordinator.data.items()
        if dev["services"].get("Camera", {}).get("available")
    )


class MieleExtrasCamera(MieleExtrasEntity, Camera):
    _attr_translation_key = "camera"

    def __init__(self, coordinator, device_id: str) -> None:
        MieleExtrasEntity.__init__(self, coordinator, device_id)
        Camera.__init__(self)
        self._attr_unique_id = f"{device_id}_camera"
        self._last_image: bytes | None = None
        self._last_fetch = 0.0
        self._last_ok: float | None = None

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        return {
            "last_fetched": (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._last_ok))
                if self._last_ok
                else None
            ),
            "note": "Kameraet leverer det sidst gemte billede; er apparatet slukket, kan det være ældre.",
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        if self._last_image and time.time() - self._last_fetch < MIN_IMAGE_INTERVAL:
            return self._last_image
        self._last_fetch = time.time()
        try:
            self._last_image = await self.coordinator.api.async_get_image(self._device_id)
            self._last_ok = time.time()
        except MieleAuthError:
            _LOGGER.error("Miele Extras: login afvist, token skal fornyes")
        except MieleApiError as err:
            _LOGGER.warning("Miele Extras kamera: %s", err)
        return self._last_image
