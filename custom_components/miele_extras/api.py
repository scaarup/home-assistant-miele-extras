"""Client for the Miele@mobile API. No Home Assistant imports, so it can be tested standalone."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import aiohttp

from . import dop2
from .const import API_BASE, CLIENT_ID, TOKEN_URL, UA_API, UA_AUTH

_LOGGER = logging.getLogger(__name__)


class MieleAuthError(Exception):
    """The refresh token was rejected (expired or revoked)."""


class MieleApiError(Exception):
    """Other errors from Miele."""


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
                    raise MieleAuthError(f"Token rejected (HTTP {resp.status})")
                resp.raise_for_status()
                body = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise MieleApiError(f"Token request failed: {err}") from err
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
                        raise MieleAuthError("Access rejected by the API")
                    resp.raise_for_status()
                    return await resp.read() if binary else await resp.json(content_type=None)
            except aiohttp.ClientError as err:
                raise MieleApiError(f"Request to {path} failed: {err}") from err
        raise MieleApiError("Unknown error")

    async def async_get_devices(self) -> dict[str, dict[str, Any]]:
        """All appliances on the account: {serial number: {"tech_type": ..., "device_type": ...}}."""
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

    async def _async_put(self, path: str, body: bytes, content_type: str) -> None:
        for attempt in (1, 2):
            token = await self._async_access_token()
            try:
                async with self._session.put(
                    f"{API_BASE}{path}",
                    data=body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": content_type,
                        "Accept": "*/*",
                        "User-Agent": UA_API,
                        "Accept-Language": "da-DK",
                    },
                    timeout=aiohttp.ClientTimeout(total=40),
                ) as resp:
                    if resp.status == 401 and attempt == 1:
                        self._access_token = None
                        continue
                    if resp.status == 401:
                        raise MieleAuthError("Access rejected by the API")
                    resp.raise_for_status()
                    return
            except aiohttp.ClientError as err:
                raise MieleApiError(f"Write to {path} failed: {err}") from err

    async def async_get_oven_process(self, device_id: str) -> dict[str, Any]:
        """Running oven program: {"program_id", "target_c", "min_c", "max_c", "adjustable"}."""
        accept = "application/vnd.miele.v1+dop2"
        state = dop2.parse(
            await self._async_get(f"/V2/Devices/{device_id}/DOP2/1/1585?idx1=0&idx2=1", accept, binary=True)
        )
        params = dop2.parse(
            await self._async_get(f"/V2/Devices/{device_id}/DOP2/1/1574?idx1=0&idx2=1", accept, binary=True)
        )
        proc = state.get(7, {})
        temp = params.get(4, {}).get(6, {})  # parameter 6 = temperature
        return {
            "program_id": proc.get(28, 0),
            "current_c": proc.get(6, {}).get(2, 0) / 100,
            "target_c": proc.get(21, {}).get(2, 0) / 100,
            "min_c": temp.get(2, 3000) / 100,
            "max_c": temp.get(3, 25000) / 100,
            "adjustable": temp.get(1, 0) != 0,
        }

    async def async_set_oven_temperature(self, device_id: str, program_id: int, celsius: float) -> None:
        body = dop2.build_oven_setpoint(program_id, round(celsius * 100))
        await self._async_put(
            f"/V2/Devices/{device_id}/DOP2/2/1577", body, "application/vnd.miele.v1+dop2"
        )
