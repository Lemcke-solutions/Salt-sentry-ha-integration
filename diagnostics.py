from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

REDACT_KEYS: set = set()


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    coordinator = entry.runtime_data
    return {
        "config": async_redact_data(dict(entry.data) | dict(entry.options), REDACT_KEYS),
        "device_data": coordinator.data,
    }
