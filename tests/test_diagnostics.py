"""Tests for diagnostics."""
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


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


async def test_diagnostics(hass):
    from custom_components.salt_sentry.diagnostics import async_get_config_entry_diagnostics

    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.salt_sentry.SaltSentryDevice") as mock_cls:
        mock_cls.return_value.get_status = AsyncMock(return_value=MOCK_STATUS)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["config"]["host"] == "192.168.1.100"
    assert result["device_data"]["unique_id"] == "e4f61f"
    assert result["device_data"]["measurement"] == 30.0
