"""Fahrenheit <-> display-unit conversion helpers.

The grill's MCU always works in Fahrenheit. Entities convert to/from
whichever temperature unit this Home Assistant instance is configured for,
using these shared helpers so climate.py and number.py stay consistent.
"""

from __future__ import annotations

from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.util.unit_conversion import TemperatureConverter


def display_unit(hass: HomeAssistant) -> str:
    """Return this HA instance's configured temperature unit."""
    return hass.config.units.temperature_unit


def to_display_unit(temp_f: float, unit: str) -> float:
    """Convert a Fahrenheit value from the grill into the display unit."""
    if unit == UnitOfTemperature.CELSIUS:
        return TemperatureConverter.convert(
            temp_f, UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS
        )
    return temp_f


def to_fahrenheit(value: float, unit: str) -> float:
    """Convert a value in the display unit back to Fahrenheit for the grill."""
    if unit == UnitOfTemperature.CELSIUS:
        return TemperatureConverter.convert(
            value, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT
        )
    return value


def bounds_to_display_unit(
    min_f: float, max_f: float, unit: str
) -> tuple[float, float]:
    """Convert Fahrenheit min/max bounds into the display unit.

    Rounded to whole degrees so Celsius bounds look clean in the UI.
    """
    if unit == UnitOfTemperature.CELSIUS:
        return (
            round(to_display_unit(min_f, unit)),
            round(to_display_unit(max_f, unit)),
        )
    return min_f, max_f
