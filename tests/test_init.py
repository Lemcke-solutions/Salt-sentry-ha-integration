"""Tests for integration setup (coordinator)."""
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pysaltsentry import SaltSentryStatus, SaltSentryConnectionError

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


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


async def test_setup_entry_success(hass):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.salt_sentry.SaltSentryDevice") as mock_cls:
        mock_cls.return_value.get_status = AsyncMock(return_value=MOCK_STATUS)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    coordinator = entry.runtime_data
    assert coordinator.data["unique_id"] == "e4f61f"
    assert coordinator.data["measurement"] == 30.0
    assert coordinator.data["firmware_version"] == "1.2.3"
    assert coordinator.data["hardware_revision"] == "A"


async def test_setup_entry_connection_error(hass):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.salt_sentry.SaltSentryDevice") as mock_cls:
        mock_cls.return_value.get_status = AsyncMock(side_effect=SaltSentryConnectionError("fail"))
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.salt_sentry.SaltSentryDevice") as mock_cls:
        mock_cls.return_value.get_status = AsyncMock(return_value=MOCK_STATUS)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
