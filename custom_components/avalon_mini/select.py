from __future__ import annotations

from datetime import timedelta  # <-- see note below
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)

# Labels shown in HA
MODE_OPTIONS = ["heating", "mining", "night"]
LEVEL_OPTIONS = ["eco", "super"]

# Map HA labels -> device indices
MODE_TO_INDEX = {
    "heating": 0,
    "mining": 1,
    "night": 2,
}

LEVEL_TO_INDEX = {
    "eco": -1,
    "super": 0,
}

# Map device indices -> HA labels
INDEX_TO_MODE = {v: k for k, v in MODE_TO_INDEX.items()}
INDEX_TO_LEVEL = {v: k for k, v in LEVEL_TO_INDEX.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Avalon Mini selects (mode, level) from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    name = data["name"]

    entities = [
        AvalonModeSelect(client, name, entry),
        AvalonLevelSelect(client, name, entry),
    ]

    async_add_entities(entities)


class AvalonModeSelect(SelectEntity):
    """Select entity for Avalon Mini mode (heating, mining, night)."""

    _attr_options = MODE_OPTIONS
    _attr_should_poll = True

    def __init__(self, client, name: str, entry: ConfigEntry) -> None:
        self._client = client
        slug = entry.entry_id
        self._attr_name = f"{name} Mode"
        self._attr_unique_id = f"{slug}_mode"
        self._current_option = "heating"

    @property
    def current_option(self) -> str:
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        """Called when user changes the option in Home Assistant."""
        if option not in MODE_TO_INDEX:
            return
        index = MODE_TO_INDEX[option]
        await self.hass.async_add_executor_job(self._client.set_mode_index, index)
        self._current_option = option
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Poll device for current mode so external changes are reflected."""
        status = await self.hass.async_add_executor_job(self._client.get_status)
        mode_index = status.get("workmode")
        if mode_index is None:
            return

        option = INDEX_TO_MODE.get(mode_index)
        if option is not None and option != self._current_option:
            self._current_option = option
            self.async_write_ha_state()


class AvalonLevelSelect(SelectEntity):
    """Select entity for Avalon Mini level (eco, super)."""

    _attr_options = LEVEL_OPTIONS
    _attr_should_poll = True

    def __init__(self, client, name: str, entry: ConfigEntry) -> None:
        self._client = client
        slug = entry.entry_id
        self._attr_name = f"{name} Level"
        self._attr_unique_id = f"{slug}_level"
        self._current_option = "eco"

    @property
    def current_option(self) -> str:
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        """Called when user changes level in Home Assistant."""
        if option not in LEVEL_TO_INDEX:
            return
        index = LEVEL_TO_INDEX[option]
        await self.hass.async_add_executor_job(self._client.set_level_index, index)
        self._current_option = option
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Poll device for current level so external changes are reflected."""
        status = await self.hass.async_add_executor_job(self._client.get_status)
        level_index = status.get("worklevel")
        if level_index is None:
            return

        option = INDEX_TO_LEVEL.get(level_index)
        if option is not None and option != self._current_option:
            self._current_option = option
            self.async_write_ha_state()
