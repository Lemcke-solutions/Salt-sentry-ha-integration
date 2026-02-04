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
            manufacturer="Salt Sentry",
            model="Salt Sentry",
            sw_version=firmware,
            configuration_url=f"http://{self.entry.data[CONF_HOST]}",
        )


class SaltDistanceSensor(SaltBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        device_id = coordinator.data.get("unique_id")
        self._attr_name = f"Salt Distance {device_id[-4:]}"
        self._attr_unique_id = f"{device_id}_distance"

    @property
    def native_value(self):
        measurement_cm = self.coordinator.data["measurement"]
        unit = self.entry.options.get(CONF_UNIT, self.entry.data[CONF_UNIT])

        if unit == UNIT_INCH:
            return round(measurement_cm / 2.54, 2)
        return measurement_cm

    @property
    def native_unit_of_measurement(self):
        unit = self.entry.options.get(CONF_UNIT, self.entry.data[CONF_UNIT])
        return "in" if unit == UNIT_INCH else "cm"


class SaltPercentageSensor(SaltBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        device_id = coordinator.data.get("unique_id")
        self._attr_name = f"Salt Level {device_id[-4:]}"
        self._attr_unique_id = f"{device_id}_percentage"
        self._attr_native_unit_of_measurement = "%"

    @property
    def native_value(self):
        measurement = self.coordinator.data["measurement"]

        config = {**self.entry.data, **self.entry.options}
        full = config[CONF_FULL]
        empty = config[CONF_EMPTY]

        if empty == full:
            return 0

        percentage = (empty - measurement) / (empty - full) * 100
        return max(0, min(100, round(percentage, 1)))


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        SaltDistanceSensor(coordinator, entry),
        SaltPercentageSensor(coordinator, entry),
    ])
