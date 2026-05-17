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
    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry

    @property
    def device_info(self) -> DeviceInfo:
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
        return {**self.entry.data, **self.entry.options}

    def _get_unit(self) -> str:
        return self._get_config().get(CONF_UNIT, UNIT_CM)

    def _get_correction_cm(self) -> float:
        config = self._get_config()
        correction: float = config.get(CONF_CORRECTION, DEFAULT_CORRECTION)
        if self._get_unit() == UNIT_INCH:
            return correction * 2.54
        return correction

    def _raw_measurement_cm(self) -> float:
        return self.coordinator.data["measurement"]

    def _corrected_measurement_cm(self) -> float:
        return max(0.0, self._raw_measurement_cm() + self._get_correction_cm())

    def _to_display_unit(self, value_cm: float) -> float:
        if self._get_unit() == UNIT_INCH:
            return round(value_cm / 2.54, 2)
        return round(value_cm, 1)

    @property
    def native_unit_of_measurement(self) -> str:
        return UnitOfLength.INCHES if self._get_unit() == UNIT_INCH else UnitOfLength.CENTIMETERS


class SaltRawDistanceSensor(SaltBaseSensor):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "raw_distance"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_raw_distance"

    @property
    def native_value(self) -> float:
        return self._to_display_unit(self._raw_measurement_cm())


class SaltDistanceSensor(SaltBaseSensor):
    _attr_translation_key = "distance"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_distance"

    @property
    def native_value(self) -> float:
        return self._to_display_unit(self._corrected_measurement_cm())


class SaltPercentageSensor(SaltBaseSensor):
    _attr_translation_key = "salt_level"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_percentage"

    @property
    def native_unit_of_measurement(self) -> str:
        return "%"

    @property
    def native_value(self) -> float:
        measurement = self._corrected_measurement_cm()
        config = self._get_config()
        full: float = config[CONF_FULL]
        empty: float = config[CONF_EMPTY]
        if empty == full:
            return 0.0
        percentage = (empty - measurement) / (empty - full) * 100
        return max(0.0, min(100.0, round(percentage, 1)))


class SaltHardwareRevisionSensor(SaltBaseSensor):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "hardware_revision"
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: DataUpdateCoordinator[dict[str, Any]], entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data['unique_id']}_hardware_revision"

    @property
    def native_unit_of_measurement(self) -> None:
        return None

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("hardware_revision", "A")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DataUpdateCoordinator[dict[str, Any]] = entry.runtime_data
    async_add_entities([
        SaltRawDistanceSensor(coordinator, entry),
        SaltDistanceSensor(coordinator, entry),
        SaltPercentageSensor(coordinator, entry),
        SaltHardwareRevisionSensor(coordinator, entry),
    ])
