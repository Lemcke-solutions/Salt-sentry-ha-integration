"""Salt Sentry sensor platform."""
from __future__ import annotations

from typing import cast

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory  # type: ignore[attr-defined]
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_EMPTY, CONF_FULL
from .coordinator import SaltSentryConfigEntry, SaltSentryCoordinator
from .entity import SaltSentryBaseSensor

PARALLEL_UPDATES = 0


class SaltRawDistanceSensor(SaltSentryBaseSensor):
    """Sensor reporting the raw (uncorrected) distance from the device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "raw_distance"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: SaltSentryCoordinator, entry: SaltSentryConfigEntry) -> None:
        """Initialize the raw distance sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_raw_distance"

    @property
    def native_value(self) -> float:
        """Return the raw distance in the configured unit."""
        return self._to_display_unit(self._raw_measurement_cm())


class SaltDistanceSensor(SaltSentryBaseSensor):
    """Sensor reporting the corrected distance from the device."""

    _attr_translation_key = "distance"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: SaltSentryCoordinator, entry: SaltSentryConfigEntry) -> None:
        """Initialize the distance sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_distance"

    @property
    def native_value(self) -> float:
        """Return the corrected distance in the configured unit."""
        return self._to_display_unit(self._corrected_measurement_cm())


class SaltPercentageSensor(SaltSentryBaseSensor):
    """Sensor reporting the salt level as a percentage."""

    _attr_translation_key = "salt_level"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SaltSentryCoordinator, entry: SaltSentryConfigEntry) -> None:
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


class SaltHardwareRevisionSensor(SaltSentryBaseSensor):
    """Sensor reporting the hardware revision of the device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "hardware_revision"

    def __init__(self, coordinator: SaltSentryCoordinator, entry: SaltSentryConfigEntry) -> None:
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
        return cast(str, self.coordinator.data.get("hardware_revision", "A"))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SaltSentryConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Salt Sentry sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([
        SaltRawDistanceSensor(coordinator, entry),
        SaltDistanceSensor(coordinator, entry),
        SaltPercentageSensor(coordinator, entry),
        SaltHardwareRevisionSensor(coordinator, entry),
    ])
