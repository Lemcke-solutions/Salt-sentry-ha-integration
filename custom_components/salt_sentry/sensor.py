"""Salt Sentry sensor platform."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import CONF_CORRECTION, CONF_EMPTY, CONF_FULL, CONF_HOST, CONF_UNIT, DEFAULT_CORRECTION, DOMAIN, UNIT_CM, UNIT_INCH

PARALLEL_UPDATES = 0


class SaltBaseSensor(CoordinatorEntity[DataUpdateCoordinator[dict[str, Any]]], SensorEntity):
    """Base class for Salt Sentry sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_id: str = self.coordinator.data["unique_id"]
        firmware: str = self.coordinator.data.get("firmware_version", "unknown")
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
        return self._get_config().get(CONF_UNIT, UNIT_CM)

    def _get_correction_cm(self) -> float:
        """Return the correction value converted to centimeters."""
        config = self._get_config()
        correction: float = config.get(CONF_CORRECTION, DEFAULT_CORRECTION)
        if self._get_unit() == UNIT_INCH:
            return correction * 2.54
        return correction

    def _raw_measurement_cm(self) -> float:
        """Return the raw distance measurement in centimeters."""
        return self.coordinator.data["measurement"]

    def _corrected_measurement_cm(self) -> float:
        """Return the corrected distance measurement in centimeters, clamped to zero."""
        return max(0.0, self._raw_measurement_cm() + self._get_correction_cm())

    def _to_display_unit(self, value_cm: float) -> float:
        """Convert a centimeter value to the configured display unit."""
        if self._get_unit() == UNIT_INCH:
            return round(value_cm / 2.54, 2)
        return round(value_cm, 1)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return UnitOfLength.INCHES if self._get_unit() == UNIT_INCH else UnitOfLength.CENTIMETERS


class SaltRawDistanceSensor(SaltBaseSensor):
    """Sensor reporting the raw (uncorrected) distance from the device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "raw_distance"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        """Initialize the raw distance sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_raw_distance"

    @property
    def native_value(self) -> float:
        """Return the raw distance in the configured unit."""
        return self._to_display_unit(self._raw_measurement_cm())


class SaltDistanceSensor(SaltBaseSensor):
    """Sensor reporting the corrected distance from the device."""

    _attr_translation_key = "distance"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        """Initialize the distance sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_distance"

    @property
    def native_value(self) -> float:
        """Return the corrected distance in the configured unit."""
        return self._to_display_unit(self._corrected_measurement_cm())


class SaltPercentageSensor(SaltBaseSensor):
    """Sensor reporting the salt level as a percentage."""

    _attr_translation_key = "salt_level"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        """Initialize the salt level sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_percentage"

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "%"

    @property
    def native_value(self) -> float:
        """Return the salt level as a percentage between 0 and 100."""
        measurement = self._corrected_measurement_cm()
        config = self._get_config()
        full: float = config[CONF_FULL]
        empty: float = config[CONF_EMPTY]
        if empty == full:
            return 0.0
        percentage = (empty - measurement) / (empty - full) * 100
        return max(0.0, min(100.0, round(percentage, 1)))


class SaltHardwareRevisionSensor(SaltBaseSensor):
    """Sensor reporting the hardware revision of the device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "hardware_revision"
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        """Initialize the hardware revision sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_hardware_revision"

    @property
    def native_unit_of_measurement(self) -> None:
        """Return no unit of measurement."""
        return None

    @property
    def native_value(self) -> str:
        """Return the hardware revision."""
        return self.coordinator.data.get("hardware_revision", "A")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Salt Sentry sensors from a config entry."""
    coordinator: DataUpdateCoordinator[dict[str, Any]] = entry.runtime_data
    async_add_entities([
        SaltRawDistanceSensor(coordinator, entry),
        SaltDistanceSensor(coordinator, entry),
        SaltPercentageSensor(coordinator, entry),
        SaltHardwareRevisionSensor(coordinator, entry),
    ])
