"""Diagnostics support for Salt Sentry."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import SaltSentryConfigEntry

REDACT_KEYS: set[str] = set()


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SaltSentryConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "config": async_redact_data(dict(entry.data) | dict(entry.options), REDACT_KEYS),
        "device_data": coordinator.data,
    }
