"""Constants for the Salt Sentry integration."""
import json
from typing import Any, cast

from homeassistant.core import HomeAssistant

DOMAIN = "salt_sentry"

CONF_HOST = "host"
CONF_UNIT = "unit"
CONF_FULL = "full_distance"
CONF_EMPTY = "empty_distance"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CORRECTION = "correction"

DEFAULT_SCAN_INTERVAL: int = 1
DEFAULT_CORRECTION: float = 0.0

UNIT_CM = "cm"
UNIT_INCH = "inch"

SOFTENER_FILE = "softeners.json"


def _load_softeners_sync(path: str) -> dict[str, Any]:
    """Load the softeners JSON file synchronously."""
    with open(path) as f:
        return cast(dict[str, Any], json.load(f))


async def async_load_softeners(hass: HomeAssistant) -> dict[str, Any]:
    """Load the softeners preset file asynchronously."""
    path = hass.config.path(f"custom_components/{DOMAIN}/{SOFTENER_FILE}")
    return await hass.async_add_executor_job(_load_softeners_sync, path)


def cm_to_unit(value_cm: float | None, unit: str) -> float | None:
    """Convert a centimeter value to the given unit."""
    if value_cm is None:
        return None
    if unit == UNIT_INCH:
        return round(value_cm / 2.54, 2)
    return value_cm
