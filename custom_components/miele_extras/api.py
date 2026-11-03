"""Klient til Miele@mobile-API. Ingen Home Assistant-importer, så den kan testes alene."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import aiohttp

from .const import API_BASE, CLIENT_ID, TOKEN_URL, UA_API, UA_AUTH

_LOGGER = logging.getLogger(__name__)


class MieleAuthError(Exception):
    """Refresh-tokenet er afvist (udløbet eller trukket tilbage)."""


class MieleApiError(Exception):
    """Andre fejl fra Miele."""


class MieleExtrasApi:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        refresh_token: str,
        on_new_refresh_token: Callable[[str], None] | None = None,
    ) -> None:
        self._session = session
        self._refresh_token = refresh_token
        self._on_new = on_new_refresh_token
        self._access_token: str | None = None
        self._expires_at = 0.0

    async def _async_access_token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 300:
            return self._access_token
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": CLIENT_ID,
        }
        try:
            async with self._session.post(
                TOKEN_URL,
                data=data,
                headers={"User-Agent": UA_AUTH, "Accept": "*/*"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status in (400, 401, 403):
                    raise MieleAuthError(f"Token afvist (HTTP {resp.status})")
                resp.raise_for_status()
                body = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise MieleApiError(f"Token-kald fejlede: {err}") from err
        self._access_token = body["access_token"]
        self._expires_at = time.time() + int(body.get("expires_in", 3600))
        new = body.get("refresh_token")
        if new and new != self._refresh_token:
            self._refresh_token = new
            if self._on_new:
                self._on_new(new)
        return self._access_token

    async def _async_get(self, path: str, accept: str, *, binary: bool = False) -> Any:
        for attempt in (1, 2):
            token = await self._async_access_token()
            try:
                async with self._session.get(
                    f"{API_BASE}{path}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": accept,
                        "User-Agent": UA_API,
                        "Accept-Language": "da-DK",
                    },
                    timeout=aiohttp.ClientTimeout(total=40),
                ) as resp:
                    if resp.status == 401 and attempt == 1:
                        self._access_token = None
                        continue
                    if resp.status == 401:
                        raise MieleAuthError("Adgang afvist af API")
                    resp.raise_for_status()
                    return await resp.read() if binary else await resp.json(content_type=None)
            except aiohttp.ClientError as err:
                raise MieleApiError(f"Kald til {path} fejlede: {err}") from err
        raise MieleApiError("Ukendt fejl")

    async def async_get_devices(self) -> dict[str, dict[str, Any]]:
        """Alle apparater på kontoen: {serienummer: {"tech_type":..., "device_type":...}}."""
        groups = await self._async_get("/V2/Devices", "application/json")
        out: dict[str, dict[str, Any]] = {}
        for group in groups if isinstance(groups, list) else []:
            for dev in group.get("devices", []):
                ident = dev.get("ident", {})
                label = ident.get("DeviceIdentLabel", {})
                dev_id = dev.get("mac") or label.get("FabNumber")
                if dev_id:
                    out[dev_id] = {
                        "tech_type": label.get("TechType") or "Miele",
                        "device_type": ident.get("DeviceType"),
                    }
        return out

    async def async_get_services(self, device_id: str) -> dict[str, Any]:
        data = await self._async_get(f"/V2/Devices/{device_id}/services", "application/json")
        return data if isinstance(data, dict) else {}

    async def async_get_image(self, device_id: str) -> bytes:
        return await self._async_get(
            f"/V2/Devices/{device_id}/services/camera/camera.jpg", "image/jpeg", binary=True
        )
