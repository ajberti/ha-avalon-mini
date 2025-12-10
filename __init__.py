from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.discovery import load_platform

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
    DEFAULT_PORT,
    DEFAULT_NAME,
)
from .avalon_api import AvalonMiniClient

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Avalon Mini integration from configuration.yaml."""
    conf = config.get(DOMAIN)
    if conf is None:
        _LOGGER.info("No configuration found for '%s' in configuration.yaml", DOMAIN)
        return True

    host = conf[CONF_HOST]
    port = conf.get(CONF_PORT, DEFAULT_PORT)
    name = conf.get(CONF_NAME, DEFAULT_NAME)

    _LOGGER.info(
        "Initializing Avalon Mini integration for %s (%s:%s)", name, host, port
    )

    client = AvalonMiniClient(host, port)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {
        "client": client,
        "name": name,
    }

    # Load platforms (YAML-based integrations)
    load_platform(hass, "switch", DOMAIN, {}, config)
    load_platform(hass, "select", DOMAIN, {}, config)
    load_platform(hass, "sensor", DOMAIN, {}, config)

    return True
