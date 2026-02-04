from datetime import timedelta
import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import *

PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Salt Sentry (YAML not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Salt Sentry from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    config = {**entry.data, **entry.options}

    session = async_get_clientsession(hass)

    async def async_update_data():
        """Fetch data from the Salt Sentry device."""
        url = f"http://{config[CONF_HOST]}/status"
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err

        if not data.get("valid", False):
            raise UpdateFailed("Device returned invalid measurement")

        unique_id = data.get("unique_id")
        if not unique_id:
            raise UpdateFailed("Device did not return a unique_id")

        distance_mm = data.get("distance_mm")
        if distance_mm is None:
            raise UpdateFailed("Device did not return a distance measurement")

        measurement_cm = distance_mm / 10

        return {
            "measurement": measurement_cm,
            "unique_id": unique_id,
            "firmware_version": data.get("firmware_version", "unknown"),
        }

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"Salt Sentry ({config[CONF_HOST]})",
        update_method=async_update_data,
        update_interval=timedelta(minutes=config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
    )

    # Eerste fetch
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward naar platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Update listener voor opties
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Reload integration when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    if DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
