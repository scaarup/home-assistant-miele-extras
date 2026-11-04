"""Camera for appliances where the app has an active camera service (e.g. the oven)."""
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
        self._fetch_failed = False

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        return {
            "last_fetched": (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._last_ok))
                if self._last_ok
                else None
            ),
            "last_fetch_failed": self._fetch_failed,
            "note": (
                "The camera serves the newest stored image; if the appliance is off it may be "
                "old. After a failed fetch no image is served (never an old one); the next "
                "request tries again."
            ),
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a fresh image, or None. Never serve an old image after a failed fetch.

        The entity stays available on purpose: an unavailable camera is never asked for an
        image again, so it could not recover by itself after a short outage.
        """
        if self._last_image and time.time() - self._last_fetch < MIN_IMAGE_INTERVAL:
            return self._last_image
        self._last_fetch = time.time()
        try:
            image = await self.coordinator.api.async_get_image(self._device_id)
        except MieleAuthError:
            _LOGGER.error("Miele Extras: login rejected, the token must be replaced")
            self._mark_failed()
            return None
        except MieleApiError as err:
            _LOGGER.warning("Miele Extras camera: %s", err)
            self._mark_failed()
            return None
        self._last_image = image
        self._last_ok = time.time()
        if self._fetch_failed:
            self._fetch_failed = False
            self.async_write_ha_state()
        return image

    def _mark_failed(self) -> None:
        self._last_image = None
        if not self._fetch_failed:
            self._fetch_failed = True
            self.async_write_ha_state()
