from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_NAME, DEFAULT_PORT, DEFAULT_NAME, PLATFORMS
from .avalon_api import AvalonMiniClient

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Avalon Mini integration (no YAML config needed)."""
    # If you want to support YAML import, you can handle DOMAIN in config here
    # and call hass.config_entries.flow.async_init(..., context={"source": SOURCE_IMPORT}, ...)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Avalon Mini from a config entry."""
    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    _LOGGER.info("Setting up Avalon Mini entry '%s' (%s:%s)", name, host, port)

    client = AvalonMiniClient(host, port)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "name": name,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry,
        [Platform.SWITCH, Platform.SELECT, Platform.SENSOR],
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Avalon Mini config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        [Platform.SWITCH, Platform.SELECT, Platform.SENSOR],
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)

    return unload_ok
