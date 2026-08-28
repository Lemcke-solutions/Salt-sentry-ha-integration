"""Tests for the options flow."""
import pytest
from unittest.mock import AsyncMock, patch
from contextlib import contextmanager
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pysaltsentry import SaltSentryStatus

from custom_components.salt_sentry.const import DOMAIN, CONF_FULL, CONF_EMPTY, CONF_SCAN_INTERVAL

MOCK_STATUS = SaltSentryStatus(
    unique_id="e4f61f",
    measurement_cm=30.0,
    firmware_version="1.2.3",
    hardware_revision="A",
)

OUT_OF_RANGE_STATUS = SaltSentryStatus(
    unique_id="e4f61f",
    measurement_cm=None,
    firmware_version="1.2.3",
    hardware_revision="A",
)

SOFTENERS_MOCK = {"other": {"name": "Other", "full_cm": None, "empty_cm": None}}

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


@contextmanager
def _patch_flow(status=MOCK_STATUS):
    with patch("custom_components.salt_sentry.config_flow.async_load_softeners", return_value=SOFTENERS_MOCK), \
         patch("custom_components.salt_sentry.config_flow.SaltSentryDevice") as mock_cls:
        mock_cls.return_value.get_status = AsyncMock(return_value=status)
        yield


async def _setup_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)
    with patch("custom_components.salt_sentry.SaltSentryDevice") as mock_cls:
        mock_cls.return_value.get_status = AsyncMock(return_value=MOCK_STATUS)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_options_flow_success(hass):
    entry = await _setup_entry(hass)

    with _patch_flow():
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"unit": "cm", "softener_type": "other"},
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "distances"
        assert result["description_placeholders"]["current_measurement"] == "30.0 cm"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_FULL: 15.0, CONF_EMPTY: 55.0, CONF_SCAN_INTERVAL: 5},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_FULL] == 15.0
        assert result["data"][CONF_EMPTY] == 55.0
        assert result["data"][CONF_SCAN_INTERVAL] == 5


async def test_options_flow_full_gt_empty_error(hass):
    entry = await _setup_entry(hass)

    with _patch_flow():
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"unit": "cm", "softener_type": "other"},
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_FULL: 55.0, CONF_EMPTY: 15.0, CONF_SCAN_INTERVAL: 5},
        )
        assert result["type"] == FlowResultType.FORM
        assert "full_distance" in result["errors"]


async def test_options_flow_out_of_range_measurement(hass):
    """An out-of-range measurement is shown as unavailable, and the flow still completes."""
    entry = await _setup_entry(hass)

    with _patch_flow(status=OUT_OF_RANGE_STATUS):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"unit": "cm", "softener_type": "other"},
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "distances"
        assert result["description_placeholders"]["current_measurement"] == "unavailable"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_FULL: 15.0, CONF_EMPTY: 55.0, CONF_SCAN_INTERVAL: 5},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
