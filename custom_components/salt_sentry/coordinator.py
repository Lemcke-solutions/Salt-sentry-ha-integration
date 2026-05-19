"""Salt Sentry data update coordinator."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pysaltsentry import SaltSentryConnectionError, SaltSentryDevice, SaltSentryInvalidDataError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SaltSentryCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for fetching Salt Sentry device data."""

    def __init__(
        self,
        hass: HomeAssistant,
        device: SaltSentryDevice,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)
        self._device = device

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Salt Sentry device."""
        try:
            status = await self._device.get_status()
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


type SaltSentryConfigEntry = ConfigEntry[SaltSentryCoordinator]
