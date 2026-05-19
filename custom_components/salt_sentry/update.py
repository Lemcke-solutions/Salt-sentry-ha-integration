"""Salt Sentry firmware update platform."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from pysaltsentry import SaltSentryDevice

from .const import CONF_HOST, DOMAIN
from .coordinator import SaltSentryConfigEntry, SaltSentryCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

GITHUB_RELEASES_URL: dict[str, str] = {
    "A": "https://api.github.com/repos/Lemcke-solutions/saltSentryFirmware/releases/latest",
    "B": "https://api.github.com/repos/Lemcke-solutions/saltSentryFirmware_rev2/releases/latest",
}
GITHUB_CHECK_INTERVAL = timedelta(hours=6)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SaltSentryConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Salt Sentry firmware update entity."""
    coordinator: SaltSentryCoordinator = entry.runtime_data
    async_add_entities([SaltSentryUpdateEntity(coordinator, entry)])


class SaltSentryUpdateEntity(CoordinatorEntity[SaltSentryCoordinator], UpdateEntity):
    """Entity that manages firmware updates for the Salt Sentry device."""

    _attr_has_entity_name = True
    _attr_translation_key = "firmware"
    _attr_supported_features = UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES

    def __init__(
        self,
        coordinator: SaltSentryCoordinator,
        entry: SaltSentryConfigEntry,
    ) -> None:
        """Initialize the firmware update entity."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{coordinator.data['unique_id']}_update"
        self._latest_version: str | None = None
        self._release_notes: str | None = None
        self._download_url: str | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(identifiers={(DOMAIN, self.coordinator.data["unique_id"])})

    @property
    def installed_version(self) -> str | None:
        """Return the currently installed firmware version."""
        return self.coordinator.data.get("firmware_version")

    @property
    def latest_version(self) -> str | None:
        """Return the latest available firmware version."""
        return self._latest_version

    async def async_release_notes(self) -> str | None:
        """Return the release notes for the latest firmware version."""
        return self._release_notes

    async def async_added_to_hass(self) -> None:
        """Fetch the latest release on startup and schedule periodic checks."""
        await super().async_added_to_hass()
        await self._fetch_latest_release()
        self.async_on_remove(
            async_track_time_interval(self.hass, self._scheduled_fetch, GITHUB_CHECK_INTERVAL)
        )

    async def _scheduled_fetch(self, _now: datetime) -> None:
        """Fetch the latest release on a scheduled interval."""
        await self._fetch_latest_release()

    async def _fetch_latest_release(self) -> None:
        """Fetch the latest firmware release from GitHub."""
        hardware_revision: str = self.coordinator.data.get("hardware_revision", "A")
        url = GITHUB_RELEASES_URL.get(hardware_revision, GITHUB_RELEASES_URL["A"])
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data: dict[str, Any] = await resp.json()
                self._latest_version = data["tag_name"].lstrip("v")
                self._release_notes = data.get("body")
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".bin"):
                        self._download_url = asset["browser_download_url"]
                        break
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.warning("Could not fetch GitHub release: %s", err)

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Download firmware from GitHub and install it on the device."""
        if not self._download_url:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="no_download_url",
            )

        config: dict[str, Any] = {**self.entry.data, **self.entry.options}
        host: str = config[CONF_HOST]
        session = async_get_clientsession(self.hass)

        async with session.get(self._download_url) as resp:
            resp.raise_for_status()
            firmware_data = await resp.read()

        await SaltSentryDevice(host, session).install_firmware(firmware_data)
        _LOGGER.info("Firmware updated successfully on %s", host)
        await self._fetch_latest_release()
