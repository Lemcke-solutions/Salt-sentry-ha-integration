from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pysaltsentry import SaltSentryDevice, SaltSentryConnectionError, SaltSentryInvalidDataError

from .const import *

PLATFORMS = ["sensor", "update"]
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    config = {**entry.data, **entry.options}
    device = SaltSentryDevice(config[CONF_HOST], async_get_clientsession(hass))

    async def async_update_data():
        try:
            status = await device.get_status()
        except SaltSentryConnectionError as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err
        except SaltSentryInvalidDataError as err:
            raise UpdateFailed(f"Invalid data from device: {err}") from err
        return {
            "measurement": status.measurement_cm,
            "unique_id": status.unique_id,
            "firmware_version": status.firmware_version,
            "hardware_revision": status.hardware_revision,
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

    entry.runtime_data = coordinator

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
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
