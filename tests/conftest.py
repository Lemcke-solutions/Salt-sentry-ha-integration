from unittest.mock import AsyncMock, patch
import pytest
from pysaltsentry import SaltSentryStatus

pytest_plugins = ["pytest_homeassistant_custom_component"]

MOCK_STATUS = SaltSentryStatus(
    unique_id="e4f61f",
    measurement_cm=30.0,
    firmware_version="1.2.3",
    hardware_revision="A",
)

MOCK_ENTRY_DATA = {
    "host": "192.168.1.100",
    "unit": "cm",
    "softener_type": "other",
    "full_distance": 10.0,
    "empty_distance": 50.0,
    "scan_interval": 1,
}


@pytest.fixture
def mock_device():
    with patch("custom_components.salt_sentry.__init__.SaltSentryDevice") as mock:
        instance = mock.return_value
        instance.get_status = AsyncMock(return_value=MOCK_STATUS)
        instance.install_firmware = AsyncMock()
        yield instance
