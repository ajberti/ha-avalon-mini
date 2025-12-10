from __future__ import annotations

from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Avalon Mini switches (power, display) from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    name = data["name"]

    entities = [
        AvalonPowerSwitch(client, name, entry),
        AvalonDisplaySwitch(client, name, entry),
    ]

    async_add_entities(entities)


class AvalonPowerSwitch(SwitchEntity):
    """Switch to control Avalon Mini power (soft on/off)."""

    _attr_icon = "mdi:power"
    _attr_should_poll = True

    def __init__(self, client, name: str, entry: ConfigEntry) -> None:
        self._client = client
        slug = entry.entry_id
        self._attr_name = f"{name} Power"
        self._attr_unique_id = f"{slug}_power"
        self._is_on = False  # best-effort tracked state

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self._client.power_on)
        # Optimistically set state; async_update will correct if needed
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self._client.power_off)
        self._is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Poll device for power state so external changes are reflected."""
        status = await self.hass.async_add_executor_job(self._client.get_status)
        system_work = status.get("system_work")

        if not system_work:
            return

        # From your observation:
        #   On  -> SYSTEMSTATU[Work: In Work, Hash Board: 1]
        #   On  -> SYSTEMSTATU[Work: In Init, Hash Board: 1]
        #   Off -> SYSTEMSTATU[Work: In Idle, Hash Board: 1]
        on_states = {"In Work", "In Init"}
        is_on = system_work in on_states

        if is_on != self._is_on:
            self._is_on = is_on
            self.async_write_ha_state()
             

class AvalonDisplaySwitch(SwitchEntity):
    """Switch to toggle the Avalon Mini display."""

    _attr_icon = "mdi:monitor"
    _attr_should_poll = True

    def __init__(self, client, name: str, entry: ConfigEntry) -> None:
        self._client = client
        slug = entry.entry_id
        self._attr_name = f"{name} Display"
        self._attr_unique_id = f"{slug}_display"
        self._is_on = True  # assume on at startup

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self._client.set_display, True)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self._client.set_display, False)
        self._is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Poll device for display state so external changes are reflected."""
        status = await self.hass.async_add_executor_job(self._client.get_status)
        lcd_on = status.get("lcd_on")
        if lcd_on is None:
            return

        is_on = lcd_on == 1
        if is_on != self._is_on:
            self._is_on = is_on
            self.async_write_ha_state()
