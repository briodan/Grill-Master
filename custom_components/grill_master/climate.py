"""Climate platform for Grill Master.

Exposes the grill as a climate entity with HEAT mode for temperature control.
Allows setting the target temperature (180-600F in 5-degree increments)
and turning the grill off.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import GrillMasterApi
from .const import (
    DOMAIN,
    MANUFACTURER,
    MAX_TEMP_F,
    MIN_TEMP_F,
    MODEL,
    TEMP_STEP_F,
)
from .coordinator import GrillMasterCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Grill Master climate entity."""
    coordinator: GrillMasterCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GrillMasterClimate(coordinator, entry)])


class GrillMasterClimate(
    CoordinatorEntity[GrillMasterCoordinator], ClimateEntity
):
    """Climate entity for controlling the grill temperature."""

    _attr_has_entity_name = True
    _attr_name = "Grill"
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_min_temp = MIN_TEMP_F
    _attr_max_temp = MAX_TEMP_F
    _attr_target_temperature_step = TEMP_STEP_F
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(
        self,
        coordinator: GrillMasterCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._api: GrillMasterApi = coordinator.api
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current grill temperature."""
        if self.coordinator.data is None:
            return None
        temp = self.coordinator.data.get("grill_temp")
        return temp if temp and temp > 0 else None

    @property
    def target_temperature(self) -> float | None:
        """Return the target (set point) temperature."""
        if self.coordinator.data is None:
            return None
        temp = self.coordinator.data.get("grill_set_temp")
        return temp if temp and temp > 0 else None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode (HEAT when on, OFF when off)."""
        if self.coordinator.data is None:
            return HVACMode.OFF
        is_on = self.coordinator.data.get("module_is_on", False)
        return HVACMode.HEAT if is_on else HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        # Round to nearest 5-degree increment
        temp_f = int(round(temperature / TEMP_STEP_F) * TEMP_STEP_F)
        temp_f = max(MIN_TEMP_F, min(MAX_TEMP_F, temp_f))

        _LOGGER.info("Setting grill temperature to %d F", temp_f)
        await self._api.set_temperature(temp_f)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode. Only OFF is actionable (turns grill off)."""
        if hvac_mode == HVACMode.OFF:
            _LOGGER.info("Turning grill off")
            await self._api.turn_off()
            await self.coordinator.async_request_refresh()
        # HEAT mode doesn't have a "turn on" command; the grill must be
        # started physically or via the set_temperature command.
