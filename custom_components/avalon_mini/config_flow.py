from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_NAME, DEFAULT_PORT, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input.

    For now we just ensure host is non-empty; we could later try a test connection.
    """
    host = data[CONF_HOST]
    if not host:
        raise ValueError("host_required")

    return {
        "title": data.get(CONF_NAME) or DEFAULT_NAME,
    }


class AvalonMiniConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Avalon Mini 3."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "invalid_host"
            else:
                # Prevent duplicate entries per host:port
                host = user_input[CONF_HOST]
                port = user_input.get(CONF_PORT, DEFAULT_PORT)

                for entry in self._async_current_entries():
                    if (
                        entry.data.get(CONF_HOST) == host
                        and entry.data.get(CONF_PORT, DEFAULT_PORT) == port
                    ):
                        return self.async_abort(reason="already_configured")

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_import(self, user_input: dict[str, Any]):
        """Handle YAML import (optional)."""
        # If you want to support `avalon_mini:` in configuration.yaml,
        # you can implement this; for now we'll just reuse async_step_user logic.
        return await self.async_step_user(user_input)
