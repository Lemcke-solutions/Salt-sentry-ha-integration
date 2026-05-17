"""Tests for the config flow."""
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pysaltsentry import SaltSentryStatus, SaltSentryConnectionError

from custom_components.salt_sentry.const import DOMAIN

MOCK_STATUS = SaltSentryStatus(
    unique_id="e4f61f",
    measurement_cm=30.0,
    firmware_version="1.2.3",
    hardware_revision="A",
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


async def test_user_flow_success(hass):
    with patch("custom_components.salt_sentry.config_flow.SaltSentryDevice") as mock_cls, \
         patch("custom_components.salt_sentry.config_flow.async_load_softeners", return_value={
             "other": {"name": "Other", "full_cm": None, "empty_cm": None}
         }):
        mock_cls.return_value.get_status = AsyncMock(return_value=MOCK_STATUS)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "unit": "cm", "softener_type": "other"},
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "distances"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"full_distance": 10.0, "empty_distance": 50.0, "scan_interval": 1},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["host"] == "192.168.1.100"


async def test_user_flow_cannot_connect(hass):
    with patch("custom_components.salt_sentry.config_flow.SaltSentryDevice") as mock_cls, \
         patch("custom_components.salt_sentry.config_flow.async_load_softeners", return_value={
             "other": {"name": "Other", "full_cm": None, "empty_cm": None}
         }):
        mock_cls.return_value.get_status = AsyncMock(side_effect=SaltSentryConnectionError("no connection"))

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "unit": "cm", "softener_type": "other"},
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_distances_full_must_be_less_than_empty(hass):
    with patch("custom_components.salt_sentry.config_flow.SaltSentryDevice") as mock_cls, \
         patch("custom_components.salt_sentry.config_flow.async_load_softeners", return_value={
             "other": {"name": "Other", "full_cm": None, "empty_cm": None}
         }):
        mock_cls.return_value.get_status = AsyncMock(return_value=MOCK_STATUS)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "unit": "cm", "softener_type": "other"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"full_distance": 50.0, "empty_distance": 10.0, "scan_interval": 1},
        )
        assert result["type"] == FlowResultType.FORM
        assert "full_distance" in result["errors"]
