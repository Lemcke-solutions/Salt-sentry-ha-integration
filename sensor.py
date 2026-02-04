from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

class SaltDistanceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_name = "Salt Distance"
        self._attr_unique_id = f"{entry.entry_id}_distance"

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


class SaltPercentageSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_name = "Salt Level"
        self._attr_unique_id = f"{entry.entry_id}_percentage"
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
