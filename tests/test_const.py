"""Tests for const helpers."""
from custom_components.salt_sentry.const import cm_to_unit, UNIT_CM, UNIT_INCH


def test_cm_to_unit_cm():
    assert cm_to_unit(10.0, UNIT_CM) == 10.0


def test_cm_to_unit_inch():
    assert cm_to_unit(25.4, UNIT_INCH) == pytest.approx(10.0, abs=0.01)


def test_cm_to_unit_none():
    assert cm_to_unit(None, UNIT_CM) is None
    assert cm_to_unit(None, UNIT_INCH) is None


import pytest


def test_cm_to_unit_reconfigure():
    result = await_not_needed = cm_to_unit(30.0, UNIT_INCH)
    assert result == pytest.approx(11.81, abs=0.01)
