"""Config flow: enter the Miele@mobile refresh token. One entry covers the whole account."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MieleApiError, MieleAuthError, MieleExtrasApi
from .const import CONF_REFRESH_TOKEN, DOMAIN


class MieleExtrasConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token = user_input[CONF_REFRESH_TOKEN].strip()
            api = MieleExtrasApi(async_get_clientsession(self.hass), token)
            try:
                devices = await api.async_get_devices()
                if not devices:
                    errors["base"] = "no_devices"
            except MieleAuthError:
                errors["base"] = "invalid_auth"
            except MieleApiError:
                errors["base"] = "cannot_connect"
            if not errors:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Miele Extras", data={CONF_REFRESH_TOKEN: token}
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_REFRESH_TOKEN): str}),
            errors=errors,
        )
