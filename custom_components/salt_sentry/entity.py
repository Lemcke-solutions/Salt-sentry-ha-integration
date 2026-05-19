"""Salt Sentry base entity."""
from __future__ import annotations

from typing import Any, cast

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfLength
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CORRECTION, CONF_HOST, CONF_UNIT, DEFAULT_CORRECTION, DOMAIN, UNIT_CM, UNIT_INCH
from .coordinator import SaltSentryConfigEntry, SaltSentryCoordinator


class SaltSentryBaseSensor(CoordinatorEntity[SaltSentryCoordinator], SensorEntity):
    """Base class for Salt Sentry sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SaltSentryCoordinator, entry: SaltSentryConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_id: str = cast(str, self.coordinator.data["unique_id"])
        firmware: str = cast(str, self.coordinator.data.get("firmware_version", "unknown"))
        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"Salt Sentry {device_id[-4:]}",
            manufacturer="Lemcke Solutions",
            model="Salt Sentry",
            sw_version=firmware,
            configuration_url=f"http://{self.entry.data[CONF_HOST]}",
        )

    def _get_config(self) -> dict[str, Any]:
        """Return merged entry data and options."""
        return {**self.entry.data, **self.entry.options}

    def _get_unit(self) -> str:
        """Return the configured display unit."""
        return cast(str, self._get_config().get(CONF_UNIT, UNIT_CM))

    def _get_correction_cm(self) -> float:
        """Return the correction value converted to centimeters."""
        config = self._get_config()
        correction: float = config.get(CONF_CORRECTION, DEFAULT_CORRECTION)
        if self._get_unit() == UNIT_INCH:
            return correction * 2.54
        return correction

    def _raw_measurement_cm(self) -> float:
        """Return the raw distance measurement in centimeters."""
        return cast(float, self.coordinator.data["measurement"])

    def _corrected_measurement_cm(self) -> float:
        """Return the corrected distance measurement in centimeters, clamped to zero."""
        return max(0.0, self._raw_measurement_cm() + self._get_correction_cm())

    def _to_display_unit(self, value_cm: float) -> float:
        """Convert a centimeter value to the configured display unit."""
        if self._get_unit() == UNIT_INCH:
            return round(value_cm / 2.54, 2)
        return round(value_cm, 1)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return UnitOfLength.INCHES if self._get_unit() == UNIT_INCH else UnitOfLength.CENTIMETERS
