from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfLength
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from .const import *

PARALLEL_UPDATES = 0


class SaltBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        device_id = self.coordinator.data.get("unique_id")
        firmware = self.coordinator.data.get("firmware_version")
        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"Salt Sentry {device_id[-4:]}",
            manufacturer="Lemcke Solutions",
            model="Salt Sentry",
            sw_version=firmware,
            configuration_url=f"http://{self.entry.data[CONF_HOST]}",
        )

    def _get_config(self):
        return {**self.entry.data, **self.entry.options}

    def _get_unit(self):
        return self._get_config().get(CONF_UNIT, UNIT_CM)

    def _get_correction_cm(self):
        config = self._get_config()
        correction = config.get(CONF_CORRECTION, DEFAULT_CORRECTION)
        if self._get_unit() == UNIT_INCH:
            return correction * 2.54
        return correction

    def _raw_measurement_cm(self):
        return self.coordinator.data["measurement"]

    def _corrected_measurement_cm(self):
        return max(0, self._raw_measurement_cm() + self._get_correction_cm())

    def _to_display_unit(self, value_cm):
        if self._get_unit() == UNIT_INCH:
            return round(value_cm / 2.54, 2)
        return round(value_cm, 1)

    @property
    def native_unit_of_measurement(self):
        return UnitOfLength.INCHES if self._get_unit() == UNIT_INCH else UnitOfLength.CENTIMETERS


class SaltRawDistanceSensor(SaltBaseSensor):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "raw_distance"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data.get('unique_id')}_raw_distance"

    @property
    def native_value(self):
        return self._to_display_unit(self._raw_measurement_cm())


class SaltDistanceSensor(SaltBaseSensor):
    _attr_translation_key = "distance"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data.get('unique_id')}_distance"

    @property
    def native_value(self):
        return self._to_display_unit(self._corrected_measurement_cm())


class SaltPercentageSensor(SaltBaseSensor):
    _attr_translation_key = "salt_level"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data.get('unique_id')}_percentage"

    @property
    def native_unit_of_measurement(self):
        return "%"

    @property
    def native_value(self):
        measurement = self._corrected_measurement_cm()
        config = self._get_config()
        full = config[CONF_FULL]
        empty = config[CONF_EMPTY]
        if empty == full:
            return 0
        percentage = (empty - measurement) / (empty - full) * 100
        return max(0, min(100, round(percentage, 1)))


class SaltHardwareRevisionSensor(SaltBaseSensor):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "hardware_revision"
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{coordinator.data.get('unique_id')}_hardware_revision"

    @property
    def native_unit_of_measurement(self):
        return None

    @property
    def native_value(self):
        return self.coordinator.data.get("hardware_revision", "A")


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([
        SaltRawDistanceSensor(coordinator, entry),
        SaltDistanceSensor(coordinator, entry),
        SaltPercentageSensor(coordinator, entry),
        SaltHardwareRevisionSensor(coordinator, entry),
    ])
