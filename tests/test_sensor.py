"""Tests for sensor value calculations."""
import pytest
from unittest.mock import MagicMock
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from custom_components.salt_sentry.sensor import SaltPercentageSensor, SaltDistanceSensor, SaltRawDistanceSensor
from custom_components.salt_sentry.const import CONF_FULL, CONF_EMPTY, CONF_UNIT, CONF_CORRECTION, UNIT_CM, UNIT_INCH


def make_sensor(sensor_class, measurement_cm, config_overrides=None):
    config = {
        CONF_FULL: 10.0,
        CONF_EMPTY: 50.0,
        CONF_UNIT: UNIT_CM,
        CONF_CORRECTION: 0.0,
        **(config_overrides or {}),
    }
    coordinator = MagicMock(spec=DataUpdateCoordinator)
    coordinator.data = {
        "measurement": measurement_cm,
        "unique_id": "test1234",
        "firmware_version": "1.0.0",
        "hardware_revision": "A",
    }
    entry = MagicMock()
    entry.data = config
    entry.options = {}
    sensor = sensor_class.__new__(sensor_class)
    sensor.coordinator = coordinator
    sensor.entry = entry
    sensor._attr_unique_id = "test"
    return sensor


class TestSaltPercentageSensor:
    def test_full_tank(self):
        sensor = make_sensor(SaltPercentageSensor, measurement_cm=10.0)
        assert sensor.native_value == 100.0

    def test_empty_tank(self):
        sensor = make_sensor(SaltPercentageSensor, measurement_cm=50.0)
        assert sensor.native_value == 0.0

    def test_half_tank(self):
        sensor = make_sensor(SaltPercentageSensor, measurement_cm=30.0)
        assert sensor.native_value == 50.0

    def test_clamped_above_100(self):
        sensor = make_sensor(SaltPercentageSensor, measurement_cm=5.0)
        assert sensor.native_value == 100.0

    def test_clamped_below_0(self):
        sensor = make_sensor(SaltPercentageSensor, measurement_cm=60.0)
        assert sensor.native_value == 0.0

    def test_equal_full_and_empty_returns_0(self):
        sensor = make_sensor(SaltPercentageSensor, measurement_cm=10.0, config_overrides={CONF_EMPTY: 10.0})
        assert sensor.native_value == 0


class TestSaltDistanceSensor:
    def test_no_correction(self):
        sensor = make_sensor(SaltDistanceSensor, measurement_cm=30.0)
        assert sensor.native_value == 30.0

    def test_positive_correction_cm(self):
        sensor = make_sensor(SaltDistanceSensor, measurement_cm=30.0, config_overrides={CONF_CORRECTION: 5.0})
        assert sensor.native_value == 35.0

    def test_negative_correction_clamped_at_zero(self):
        sensor = make_sensor(SaltDistanceSensor, measurement_cm=2.0, config_overrides={CONF_CORRECTION: -5.0})
        assert sensor.native_value == 0.0

    def test_inch_conversion(self):
        sensor = make_sensor(SaltDistanceSensor, measurement_cm=25.4, config_overrides={CONF_UNIT: UNIT_INCH})
        assert sensor.native_value == pytest.approx(10.0, abs=0.01)

    def test_inch_correction_converted(self):
        # Correction of 1 inch = 2.54 cm
        sensor = make_sensor(
            SaltDistanceSensor,
            measurement_cm=25.4,
            config_overrides={CONF_UNIT: UNIT_INCH, CONF_CORRECTION: 1.0},
        )
        # 25.4cm + 2.54cm = 27.94cm → 11.0 inch
        assert sensor.native_value == pytest.approx(11.0, abs=0.01)


class TestSaltRawDistanceSensor:
    def test_returns_raw_measurement(self):
        sensor = make_sensor(SaltRawDistanceSensor, measurement_cm=30.0, config_overrides={CONF_CORRECTION: 5.0})
        assert sensor.native_value == 30.0

    def test_disabled_by_default(self):
        sensor = make_sensor(SaltRawDistanceSensor, measurement_cm=30.0)
        assert sensor.entity_registry_enabled_default is False
