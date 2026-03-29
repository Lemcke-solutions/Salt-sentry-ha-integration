from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import *


class SaltBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Salt Sentry sensors."""

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
        """Geeft de correctie altijd terug in cm, ongeacht de gekozen eenheid."""
        config = self._get_config()
        correction = config.get(CONF_CORRECTION, DEFAULT_CORRECTION)
        if self._get_unit() == UNIT_INCH:
            return correction * 2.54
        return correction

    def _raw_measurement_cm(self):
        return self.coordinator.data["measurement"]

    def _corrected_measurement_cm(self):
        return self._raw_measurement_cm() + self._get_correction_cm()

    def _to_display_unit(self, value_cm):
        if self._get_unit() == UNIT_INCH:
            return round(value_cm / 2.54, 2)
        return round(value_cm, 1)

    @property
    def native_unit_of_measurement(self):
        return "in" if self._get_unit() == UNIT_INCH else "cm"


class SaltRawDistanceSensor(SaltBaseSensor):
    """Ruwe meting direct van de sensor, zonder correctie."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        device_id = coordinator.data.get("unique_id")
        self._attr_name = f"Salt Distance raw{device_id[-4:]}"
        self._attr_unique_id = f"{device_id}_raw_distance"

    @property
    def native_value(self):
        return self._to_display_unit(self._raw_measurement_cm())


class SaltDistanceSensor(SaltBaseSensor):
    """Gecorrigeerde afstandsmeting."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        device_id = coordinator.data.get("unique_id")
        self._attr_name = f"Salt Distance {device_id[-4:]}"
        self._attr_unique_id = f"{device_id}_distance"

    @property
    def native_value(self):
        return self._to_display_unit(self._corrected_measurement_cm())


class SaltPercentageSensor(SaltBaseSensor):
    """Zoutniveau in procenten, berekend op basis van gecorrigeerde meting."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        device_id = coordinator.data.get("unique_id")
        self._attr_name = f"Salt Level {device_id[-4:]}"
        self._attr_unique_id = f"{device_id}_percentage"
        self._attr_native_unit_of_measurement = "%"

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


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        SaltRawDistanceSensor(coordinator, entry),
        SaltDistanceSensor(coordinator, entry),
        SaltPercentageSensor(coordinator, entry),
    ])