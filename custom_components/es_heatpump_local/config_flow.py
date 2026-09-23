"""Config flow for ES Heatpump Local."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.helpers import config_validation as cv

from .const import CONF_HOST, DEFAULT_HOST, DEFAULT_PORT, DOMAIN


class ESHeatpumpLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle UI and YAML-import setup for the local TCP listener."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle manual setup."""
        if user_input is not None:
            return await self._create_entry(user_input)

        return self.async_show_form(step_id="user", data_schema=_schema())

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> config_entries.FlowResult:
        """Handle YAML import."""
        return await self._create_entry(import_data)

    async def _create_entry(self, data: dict[str, Any]) -> config_entries.FlowResult:
        unique_id = f"{data[CONF_HOST]}:{data[CONF_PORT]}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(updates=data)

        return self.async_create_entry(
            title=f"ES Heatpump Local ({data[CONF_HOST]}:{data[CONF_PORT]})",
            data=data,
        )


def _schema() -> vol.Schema:
    """Return the config flow form schema."""
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=DEFAULT_HOST): cv.string,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        }
    )
