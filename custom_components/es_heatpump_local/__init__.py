"""ES Heatpump Local integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import CONF_HOST, DEFAULT_HOST, DEFAULT_PORT, DOMAIN, PLATFORMS
from .coordinator import ESHeatpumpLocalCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {
                vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Import YAML config into a config entry."""
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=config[DOMAIN],
            )
        )

    async def test_dhw_target(call):
        coordinators = list(hass.data.get(DOMAIN, {}).values())
        if len(coordinators) != 1:
            raise HomeAssistantError("Need exactly one loaded heat pump integration")
        try:
            return await coordinators[0].async_test_dhw_target(
                call.data["temperature"], call.data["expected_temperature"])
        except (ValueError, ConnectionError, TimeoutError) as err:
            raise HomeAssistantError(str(err)) from err

    hass.services.async_register(
        DOMAIN, "test_dhw_target", test_dhw_target,
        schema=vol.Schema({vol.Required("temperature"): vol.In([49, 50]),
                           vol.Required("expected_temperature"): vol.In([49, 50])}),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, "set_dhw_target", test_dhw_target,
        schema=vol.Schema({vol.Required("temperature"): vol.All(vol.Coerce(float), vol.Range(min=45, max=55)),
                           vol.Required("expected_temperature"): vol.All(vol.Coerce(float), vol.Range(min=45, max=55))}),
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    coordinator = ESHeatpumpLocalCoordinator(
        hass=hass,
        host=entry.data.get(CONF_HOST, DEFAULT_HOST),
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
    )

    try:
        await coordinator.async_start()
    except OSError as err:
        raise ConfigEntryNotReady(
            f"Could not bind ES Heatpump Local listener on "
            f"{entry.data.get(CONF_HOST, DEFAULT_HOST)}:{entry.data.get(CONF_PORT, DEFAULT_PORT)}: {err}"
        ) from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    coordinator: ESHeatpumpLocalCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.async_stop()

    return unload_ok
