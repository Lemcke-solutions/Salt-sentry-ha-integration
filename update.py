from datetime import timedelta
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp
import logging
from .const import *

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

GITHUB_RELEASES_URL = {
    "A": "https://api.github.com/repos/Lemcke-solutions/saltSentryFirmware/releases/latest",
    "B": "https://api.github.com/repos/Lemcke-solutions/saltSentryFirmware_rev2/releases/latest",
}
GITHUB_CHECK_INTERVAL = timedelta(hours=6)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([SaltSentryUpdateEntity(coordinator, entry)])


class SaltSentryUpdateEntity(CoordinatorEntity, UpdateEntity):

    _attr_has_entity_name = True
    _attr_translation_key = "firmware"
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
    )

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        device_id = coordinator.data.get("unique_id")
        self._attr_unique_id = f"{device_id}_update"
        self._latest_version = None
        self._release_notes = None
        self._download_url = None

    @property
    def device_info(self):
        from homeassistant.helpers.device_registry import DeviceInfo
        device_id = self.coordinator.data.get("unique_id")
        return DeviceInfo(identifiers={(DOMAIN, device_id)})

    @property
    def installed_version(self):
        return self.coordinator.data.get("firmware_version")

    @property
    def latest_version(self):
        return self._latest_version

    async def async_release_notes(self) -> str | None:
        return self._release_notes

    async def async_added_to_hass(self):
        """Wordt aangeroepen zodra de entity geladen is — haal direct de laatste versie op."""
        await super().async_added_to_hass()
        await self._fetch_latest_release()

        # Daarna elke 6 uur opnieuw checken
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._scheduled_fetch,
                GITHUB_CHECK_INTERVAL,
            )
        )

    async def _scheduled_fetch(self, _now):
        """Wrapper voor de periodieke check (krijgt een datetime argument mee)."""
        await self._fetch_latest_release()

    async def _fetch_latest_release(self):
        """Haal de laatste release op van GitHub."""
        hardware_revision = self.coordinator.data.get("hardware_revision", "A")
        url = GITHUB_RELEASES_URL.get(hardware_revision, GITHUB_RELEASES_URL["A"])
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                self._latest_version = data["tag_name"].lstrip("v")
                self._release_notes = data.get("body")
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".bin"):
                        self._download_url = asset["browser_download_url"]
                        break
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.warning("Kon GitHub release niet ophalen: %s", err)

    async def async_install(self, version, backup, **kwargs):
        """Download firmware van GitHub en push naar apparaat via /update."""
        if not self._download_url:
            raise Exception("Geen download URL beschikbaar")

        config = {**self.entry.data, **self.entry.options}
        host = config[CONF_HOST]

        session = async_get_clientsession(self.hass)

        # Download de .bin van GitHub
        async with session.get(self._download_url) as resp:
            resp.raise_for_status()
            firmware_data = await resp.read()

        # Push naar het apparaat
        upload_url = f"http://{host}/update"
        data = aiohttp.FormData()
        data.add_field("firmware", firmware_data,
                       filename="firmware.bin",
                       content_type="application/octet-stream")

        async with session.post(upload_url, data=data) as resp:
            if resp.status != 200:
                raise Exception(f"OTA mislukt, status: {resp.status}")

        _LOGGER.info("Firmware update succesvol naar %s", host)

        # Versie opnieuw ophalen na update
        await self._fetch_latest_release()
