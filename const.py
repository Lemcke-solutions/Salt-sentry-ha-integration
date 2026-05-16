import json
import os

DOMAIN = "salt_sentry"

CONF_HOST = "host"
CONF_UNIT = "unit"
CONF_FULL = "full_distance"
CONF_EMPTY = "empty_distance"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CORRECTION = "correction"

DEFAULT_SCAN_INTERVAL = 1  # minutes
DEFAULT_CORRECTION = 0.0

UNIT_CM = "cm"
UNIT_INCH = "inch"

SOFTENER_FILE = "softeners.json"


def _load_softeners_sync(path):
    with open(path, "r") as f:
        return json.load(f)


async def async_load_softeners(hass):
    path = hass.config.path(f"custom_components/{DOMAIN}/{SOFTENER_FILE}")
    return await hass.async_add_executor_job(_load_softeners_sync, path)


def cm_to_unit(value_cm, unit):
    if value_cm is None:
        return None
    if unit == UNIT_INCH:
        return round(value_cm / 2.54, 2)
    return value_cm