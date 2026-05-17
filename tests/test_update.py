"""Tests for the firmware update entity."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pysaltsentry import SaltSentryStatus

from custom_components.salt_sentry.const import DOMAIN

MOCK_STATUS = SaltSentryStatus(
    unique_id="e4f61f",
    measurement_cm=30.0,
    firmware_version="1.2.3",
    hardware_revision="A",
)

ENTRY_DATA = {
    "host": "192.168.1.100",
    "unit": "cm",
    "softener_type": "other",
    "full_distance": 10.0,
    "empty_distance": 50.0,
    "scan_interval": 1,
}

GITHUB_RELEASE = {
    "tag_name": "v1.3.0",
    "body": "Bug fixes",
    "assets": [{"name": "firmware.bin", "browser_download_url": "http://example.com/firmware.bin"}],
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


async def _setup_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)
    with patch("custom_components.salt_sentry.SaltSentryDevice") as mock_cls, \
         patch("custom_components.salt_sentry.update.async_get_clientsession") as mock_session_fn:
        mock_cls.return_value.get_status = AsyncMock(return_value=MOCK_STATUS)

        mock_resp = AsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = AsyncMock(return_value=GITHUB_RELEASE)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)
        mock_session_fn.return_value = mock_session

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_update_entity_latest_version(hass):
    entry = await _setup_entry(hass)
    state = hass.states.get("update.salt_sentry_f61f_firmware")
    assert state is not None
    assert state.attributes.get("latest_version") == "1.3.0"
    assert state.attributes.get("installed_version") == "1.2.3"


async def test_update_entity_install(hass):
    entry = await _setup_entry(hass)

    with patch("custom_components.salt_sentry.update.async_get_clientsession") as mock_session_fn, \
         patch("custom_components.salt_sentry.update.SaltSentryDevice") as mock_device_cls:

        mock_fw_resp = AsyncMock()
        mock_fw_resp.raise_for_status = MagicMock()
        mock_fw_resp.read = AsyncMock(return_value=b"firmware_bytes")
        mock_fw_resp.__aenter__ = AsyncMock(return_value=mock_fw_resp)
        mock_fw_resp.__aexit__ = AsyncMock(return_value=False)

        mock_gh_resp = AsyncMock()
        mock_gh_resp.raise_for_status = MagicMock()
        mock_gh_resp.json = AsyncMock(return_value=GITHUB_RELEASE)
        mock_gh_resp.__aenter__ = AsyncMock(return_value=mock_gh_resp)
        mock_gh_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=[mock_fw_resp, mock_gh_resp])
        mock_session_fn.return_value = mock_session

        mock_device_cls.return_value.install_firmware = AsyncMock()

        entity_id = "update.salt_sentry_f61f_firmware"
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": entity_id},
            blocking=True,
        )

        mock_device_cls.return_value.install_firmware.assert_called_once_with(b"firmware_bytes")


async def test_update_fetch_failure_logged(hass):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.salt_sentry.SaltSentryDevice") as mock_cls, \
         patch("custom_components.salt_sentry.update.async_get_clientsession") as mock_session_fn:
        mock_cls.return_value.get_status = AsyncMock(return_value=MOCK_STATUS)

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("network error"))
        mock_session_fn.return_value = mock_session

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("update.salt_sentry_f61f_firmware")
    assert state is not None
    assert state.attributes.get("latest_version") is None
