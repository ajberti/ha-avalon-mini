from __future__ import annotations

from typing import Dict

from datetime import timedelta
import logging
import re

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# How often Home Assistant will call async_update on these sensors
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Avalon Mini sensors (hashrate, ambient temp, target temp) from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    name = data["name"]

    entities = [
        AvalonHashrateSensor(client, name, entry),
        AvalonAmbientTemperatureSensor(client, name, entry),
        AvalonTargetTemperatureSensor(client, name, entry),
    ]

    async_add_entities(entities)


# ---------- Helper: parse cgminer-style KV from SUMMARY ----------


def _parse_cgminer_kv(raw: str) -> Dict[str, str]:
    """
    Parse a cgminer-style response string into a flat dict of key->value.

    Example input:
      STATUS=...|SUMMARY,Elapsed=558,MHS av=32581844.99,MHS 5s=36807196.51,...

    We:
      - split on '|'
      - split each part on ','
      - split each item on '='
      - build a dict of last-seen key=value
    """
    result: Dict[str, str] = {}

    if not raw:
        return result

    for section in raw.split("|"):
        for item in section.split(","):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key:
                result[key] = value

    return result


# ---------- Hashrate sensor (MH/s) ----------


class AvalonHashrateSensor(SensorEntity):
    """Reports hashrate based on cgminer 'summary' output."""

    _attr_native_unit_of_measurement = "MH/s"
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
        """Fetch latest summary data from the miner and update hashrate."""
        raw = await self.hass.async_add_executor_job(self._client.summary)
        data = _parse_cgminer_kv(raw)

        # We know the keys look like:
        #   MHS av=32581844.99
        #   MHS 5s=36807196.51
        #   MHS 1m=...
        #   etc.
        keys_in_preference = [
            "MHS 5s",
            "MHS av",
            "MHS 1m",
            "MHS 5m",
            "MHS 15m",
        ]

        value = None
        chosen_key = None

        for k in keys_in_preference:
            if k in data:
                value = data[k]
                chosen_key = k
                break

        if value is None:
            _LOGGER.debug("No known hashrate key found in summary: %s", data)
            self._native_value = None
            return

        try:
            mh_s = float(value)
        except (TypeError, ValueError):
            _LOGGER.warning(
                "Failed to parse hashrate value '%s' for key '%s'",
                value,
                chosen_key,
            )
            self._native_value = None
            return

        # Keep in MH/s (nice human-friendly numbers)
        self._native_value = mh_s

        _LOGGER.debug(
            "Parsed hashrate from key '%s' value '%s' => %s MH/s",
            chosen_key,
            value,
            self._native_value,
        )


# ---------- Ambient temperature sensor (TA[xx]) ----------


class AvalonAmbientTemperatureSensor(SensorEntity):
    """Reports ambient temperature (TA) from cgminer 'estats' output."""

    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:thermometer"
    _attr_should_poll = True

    def __init__(self, client, name: str, entry: ConfigEntry) -> None:
        self._client = client
        slug = entry.entry_id
        self._attr_name = f"{name} Ambient Temperature"
        self._attr_unique_id = f"{slug}_ambient_temperature"
        self._native_value: float | None = None

    @property
    def native_value(self) -> float | None:
        return self._native_value

    async def async_update(self) -> None:
        """Fetch latest extended stats and update ambient temperature."""
        raw = await self.hass.async_add_executor_job(self._client.estats)

        # estats contains e.g.: ... TA[66] ...
        m = re.search(r"TA\[(\d+(\.\d+)?)\]", raw)
        if not m:
            _LOGGER.debug("No TA[...] (ambient temp) found in estats: %s", raw)
            self._native_value = None
            return

        value = m.group(1)
        try:
            temp = float(value)
        except (TypeError, ValueError):
            _LOGGER.warning("Failed to parse ambient temp value '%s' from TA[]", value)
            self._native_value = None
            return

        self._native_value = temp
        _LOGGER.debug("Parsed ambient temperature TA[%s] => %.2f °C", value, temp)


# ---------- Target temperature sensor (TarT[xx]) ----------


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
        """Fetch latest extended stats and update target temperature."""
        raw = await self.hass.async_add_executor_job(self._client.estats)

        # estats contains e.g.: ... TarT[90] ...
        m = re.search(r"TarT\[(\d+(\.\d+)?)\]", raw)
        if not m:
            _LOGGER.debug("No TarT[...] (target temp) found in estats: %s", raw)
            self._native_value = None
            return

        value = m.group(1)
        try:
            temp = float(value)
        except (TypeError, ValueError):
            _LOGGER.warning("Failed to parse TarT (target temp) value '%s'", value)
            self._native_value = None
            return

        self._native_value = temp
        _LOGGER.debug("Parsed target temperature TarT[%s] => %.2f °C", value, temp)
