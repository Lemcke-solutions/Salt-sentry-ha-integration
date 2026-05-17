"""Tests for zeroconf discovery."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pysaltsentry import SaltSentryStatus

from custom_components.salt_sentry.const import DOMAIN

MOCK_STATUS = SaltSentryStatus(
    unique_id="e4f61f",
    measurement_cm=30.0,
    firmware_version="1.2.3",
    hardware_revision="A",
)

SOFTENERS_MOCK = {"other": {"name": "Other", "full_cm": None, "empty_cm": None}}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


def _make_discovery_info(host: str = "192.168.1.100", device_id: str = "e4f61f"):
    info = MagicMock()
    info.host = host
    info.properties = {"id": device_id}
    return info


async def test_zeroconf_confirm_and_complete(hass):
    with patch("custom_components.salt_sentry.config_flow.SaltSentryDevice") as mock_cls, \
         patch("custom_components.salt_sentry.config_flow.async_load_softeners", return_value=SOFTENERS_MOCK):
        mock_cls.return_value.get_status = AsyncMock(return_value=MOCK_STATUS)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=_make_discovery_info(),
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "zeroconf_confirm"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
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


async def test_zeroconf_aborts_if_already_configured(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.100"},
        unique_id="e4f61f",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=_make_discovery_info(),
    )
    assert result["type"] == FlowResultType.ABORT
