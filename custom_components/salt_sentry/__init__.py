"""Salt Sentry integration."""
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntry
from pysaltsentry import SaltSentryDevice

from .const import CONF_HOST, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import SaltSentryConfigEntry, SaltSentryCoordinator

PLATFORMS: list[str] = ["sensor", "update"]


async def async_setup_entry(hass: HomeAssistant, entry: SaltSentryConfigEntry) -> bool:
    """Set up Salt Sentry from a config entry."""
    config = {**entry.data, **entry.options}
    device = SaltSentryDevice(config[CONF_HOST], async_get_clientsession(hass))
    coordinator = SaltSentryCoordinator(
        hass,
        device,
        timedelta(minutes=config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def update_listener(hass: HomeAssistant, entry: SaltSentryConfigEntry) -> None:
    """Reload the config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: SaltSentryConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: SaltSentryConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow the user to remove the device from the device registry."""
    return True
