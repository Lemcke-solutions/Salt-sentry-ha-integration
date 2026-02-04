from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import *

class SaltDistanceSensor(CoordinatorEntity, SensorEntity):
    """Sensor voor de gemeten afstand van de Salt Sentry."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_distance"
        self._attr_name = f"Salt Distance {self.coordinator.data['unique_id'][-4:]}"

    @property
    def device_info(self) -> DeviceInfo:
        """Geef device info terug zodat HA apparaten kan groeperen."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data["unique_id"])},
            name=f"Salt Sentry {self.coordinator.data['unique_id'][-4:]}",
            manufacturer="Salt Sentry",
            model="Salt Sentry",
            sw_version=self.coordinator.data.get("firmware_version", "unknown"),
        )

    @property
    def native_value(self):
        """Afstand in cm of inch, afhankelijk van config."""
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
    """Sensor voor het zoutpercentage in de bak."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_percentage"
        self._attr_name = f"Salt Level {self.coordinator.data['unique_id'][-4:]}"
        self._attr_native_unit_of_measurement = "%"

    @property
    def native_value(self):
        """Bereken zoutpercentage op basis van full/empty config."""
        measurement = self.coordinator.data["measurement"]
        config = {**self.entry.data, **self.entry.options}
        full = float(config[CONF_FULL])
        empty = float(config[CONF_EMPTY])

        if empty == full:
            return 0

        percentage = (empty - measurement) / (empty - full) * 100
        return max(0, min(100, round(percentage, 1)))


async def async_setup_entry(hass, entry, async_add_entities):
    """Voeg de sensors toe bij setup van de config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        SaltDistanceSensor(coordinator, entry),
        SaltPercentageSensor(coordinator, entry),
    ])
