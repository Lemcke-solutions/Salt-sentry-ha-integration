from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from pysaltsentry import SaltSentryDevice

from .const import CONF_HOST, DOMAIN

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

GITHUB_RELEASES_URL: dict[str, str] = {
    "A": "https://api.github.com/repos/Lemcke-solutions/saltSentryFirmware/releases/latest",
    "B": "https://api.github.com/repos/Lemcke-solutions/saltSentryFirmware_rev2/releases/latest",
}
GITHUB_CHECK_INTERVAL = timedelta(hours=6)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DataUpdateCoordinator[dict[str, Any]] = entry.runtime_data
    async_add_entities([SaltSentryUpdateEntity(coordinator, entry)])


class SaltSentryUpdateEntity(CoordinatorEntity[DataUpdateCoordinator[dict[str, Any]]], UpdateEntity):

    _attr_has_entity_name = True
    _attr_translation_key = "firmware"
    _attr_supported_features = UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, Any]],
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{coordinator.data['unique_id']}_update"
        self._latest_version: str | None = None
        self._release_notes: str | None = None
        self._download_url: str | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.coordinator.data["unique_id"])})

    @property
    def installed_version(self) -> str | None:
        return self.coordinator.data.get("firmware_version")

    @property
    def latest_version(self) -> str | None:
        return self._latest_version

    async def async_release_notes(self) -> str | None:
        return self._release_notes

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._fetch_latest_release()
        self.async_on_remove(
            async_track_time_interval(self.hass, self._scheduled_fetch, GITHUB_CHECK_INTERVAL)
        )

    async def _scheduled_fetch(self, _now: datetime) -> None:
        await self._fetch_latest_release()

    async def _fetch_latest_release(self) -> None:
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
        if not self._download_url:
            raise RuntimeError("No download URL available")

        config: dict[str, Any] = {**self.entry.data, **self.entry.options}
        host: str = config[CONF_HOST]
        session = async_get_clientsession(self.hass)

        async with session.get(self._download_url) as resp:
            resp.raise_for_status()
            firmware_data = await resp.read()

        await SaltSentryDevice(host, session).install_firmware(firmware_data)
        _LOGGER.info("Firmware updated successfully on %s", host)
        await self._fetch_latest_release()
