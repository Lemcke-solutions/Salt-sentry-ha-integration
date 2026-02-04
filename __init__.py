from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
import aiohttp
import logging

from .const import *

PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    config = {**entry.data, **entry.options}

    async def async_update_data():
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{config[CONF_HOST]}/status") as resp:
                resp.raise_for_status()
                data = await resp.json()

                if not data.get("valid", False):
                    raise ValueError("Invalid measurement from device")

                distance_mm = data.get("distance_mm")
                measurement_cm = distance_mm / 10

                return {
                    "measurement": measurement_cm,
                    "unique_id": data.get("unique_id"),
                    "firmware_version": data.get("firmware_version"),
                }

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(
            minutes=config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def update_listener(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
