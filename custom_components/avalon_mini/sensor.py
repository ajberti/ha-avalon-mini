from __future__ import annotations

from typing import Dict, List

from datetime import timedelta
import logging
import re


from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# How often Home Assistant will poll for state (summary/estats)
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Avalon Mini sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    name = data["name"]

    entities = [
        AvalonHashrateSensor(client, name, entry),
        AvalonRoomTemperatureSensor(client, name, entry),
        AvalonTargetTemperatureSensor(client, name, entry),
        AvalonPowerDrawSensor(client, name, entry),
    ]

    async_add_entities(entities)


# ---------- Helper: parse cgminer-style KV from SUMMARY ----------


def _parse_cgminer_kv(raw: str) -> Dict[str, str]:
    """Parse cgminer-style response into a simple dict."""
    result: Dict[str, str] = {}
    if not raw:
        return result

    for section in raw.split("|"):
        for item in section.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                result[key.strip()] = value.strip()

    return result


# ---------- Hashrate sensor ----------


class AvalonHashrateSensor(SensorEntity):
    """Reports hashrate (TH/s) from cgminer 'summary' output."""

    _attr_native_unit_of_measurement = "TH/s"
    _attr_icon = "mdi:pickaxe"
    _attr_should_poll = True

    def __init__(self, client, name: str, entry: ConfigEntry) -> None:
        self._client = client
        slug = entry.entry_id
        self._attr_name = f"{name} Hashrate"
        self._attr_unique_id = f"{slug}_hashrate"
        self._native_value: float | None = None

    @property
    def native_value(self) -> float | None:
        return self._native_value

    async def async_update(self) -> None:
        raw = await self.hass.async_add_executor_job(self._client.summary)
        data = _parse_cgminer_kv(raw)

        # Prioritize these keys in order
        keys = ["MHS 5s", "MHS av", "MHS 1m", "MHS 5m", "MHS 15m"]

        value = None
        chosen_key = None
        for key in keys:
            if key in data:
                value = data[key]
                chosen_key = key
                break

        if value is None:
            _LOGGER.debug("No hashrate key found in summary: %s", data)
            self._native_value = None
            return

        try:
            mh_s = float(value)  # value is in MH/s
        except ValueError:
            _LOGGER.warning(
                "Cannot parse hashrate value '%s' (key '%s')", value, chosen_key
            )
            self._native_value = None
            return

        # Convert MH/s → TH/s
        th_s = mh_s / 1_000_000.0

        # Round to 2 decimals for nice dashboard display
        self._native_value = round(th_s, 2)

        _LOGGER.debug(
            "Parsed hashrate from %s = %.2f TH/s (raw %.2f MH/s)",
            chosen_key,
            self._native_value,
            mh_s,
        )


# ---------- Room temperature sensor (ITemp) ----------


class AvalonRoomTemperatureSensor(SensorEntity):
    """Reports the inlet / room temperature (ITemp) from estats."""

    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:thermometer"
    _attr_should_poll = True

    def __init__(self, client, name: str, entry: ConfigEntry) -> None:
        self._client = client
        slug = entry.entry_id
        self._attr_name = f"{name} Room Temperature"
        self._attr_unique_id = f"{slug}_room_temperature"
        self._native_value: float | None = None

    @property
    def native_value(self) -> float | None:
        return self._native_value

    async def async_update(self) -> None:
        """Parse ITemp[...] from estats."""
        raw = await self.hass.async_add_executor_job(self._client.estats)

        # estats includes e.g. ITemp[31]
        m = re.search(r"ITemp\[(\d+(\.\d+)?)\]", raw)
        if not m:
            _LOGGER.debug("No ITemp[...] value found in estats: %s", raw)
            self._native_value = None
            return

        try:
            temp = float(m.group(1))
        except ValueError:
            _LOGGER.warning("Failed to parse ITemp value '%s'", m.group(1))
            self._native_value = None
            return

        self._native_value = temp
        _LOGGER.debug("Parsed room temperature ITemp => %.2f°C", temp)


# ---------- Target temperature sensor (TarT) ----------


class AvalonTargetTemperatureSensor(SensorEntity):
    """Reports the target temperature (TarT) set via the Avalon app."""

    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:thermometer-check"
    _attr_should_poll = True

    def __init__(self, client, name: str, entry: ConfigEntry) -> None:
        self._client = client
        slug = entry.entry_id
        self._attr_name = f"{name} Target Temperature"
        self._attr_unique_id = f"{slug}_target_temperature"
        self._native_value: float | None = None

    @property
    def native_value(self) -> float | None:
        return self._native_value

    async def async_update(self) -> None:
        """Parse TarT[...] from estats."""
        raw = await self.hass.async_add_executor_job(self._client.estats)

        m = re.search(r"TarT\[(\d+(\.\d+)?)\]", raw)
        if not m:
            _LOGGER.debug("No TarT[...] value found in estats: %s", raw)
            self._native_value = None
            return

        try:
            temp = float(m.group(1))
        except ValueError:
            _LOGGER.warning("Failed to parse TarT value '%s'", m.group(1))
            self._native_value = None
            return

        self._native_value = temp
        _LOGGER.debug("Parsed target temperature TarT => %.2f°C", temp)


# ---------- Power draw sensor (PS[...]) ----------


class AvalonPowerDrawSensor(SensorEntity):
    """Reports estimated power draw in watts from the PS[...] field."""

    _attr_native_unit_of_measurement = "W"
    _attr_icon = "mdi:flash"
    _attr_should_poll = True

    def __init__(self, client, name: str, entry: ConfigEntry) -> None:
        self._client = client
        slug = entry.entry_id
        self._attr_name = f"{name} Power Draw"
        self._attr_unique_id = f"{slug}_power_draw"
        self._native_value: float | None = None

    @property
    def native_value(self) -> float | None:
        return self._native_value

    async def async_update(self) -> None:
        """
        Parse PS[...] from estats and use one of the values as watts.

        Example estats fragment:
          PS[0 1215 2034 37 756 2032 808]

        Based on observation, the 5th value (index 4) appears to represent
        power draw in watts (~756 W here). If you discover official docs or
        different mapping, adjust the index below.
        """
        raw = await self.hass.async_add_executor_job(self._client.estats)

        m = re.search(r"PS\[(.*?)\]", raw)
        if not m:
            _LOGGER.debug("No PS[...] field found in estats: %s", raw)
            self._native_value = None
            return

        contents = m.group(1).strip()
        if not contents:
            _LOGGER.debug("Empty PS[...] contents in estats: %s", raw)
            self._native_value = None
            return

        parts: List[str] = contents.split()
        # Need at least 5 elements to read index 4 safely
        if len(parts) < 5:
            _LOGGER.debug("Unexpected PS format '%s' (need >=5 values)", contents)
            self._native_value = None
            return

        # Use index 4 as power in watts (e.g. '756' in the example above)
        power_str = parts[4]

        try:
            watts = float(power_str)
        except ValueError:
            _LOGGER.warning(
                "Failed to parse power value '%s' from PS[%s]", power_str, contents
            )
            self._native_value = None
            return

        self._native_value = watts
        _LOGGER.debug("Parsed power draw from PS[...] => %.1f W", watts)
