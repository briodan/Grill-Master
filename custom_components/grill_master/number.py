"""Number platform for Grill Master.

Exposes Probe 1's target (done) temperature as a settable number entity.
Only Probe 1 has a settable target on the LBL control board (LG1000BL) -
the MCU has no equivalent command for probes 2+.
"""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import GrillMasterApi
from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    PROBE_TARGET_MAX_F,
    PROBE_TARGET_MIN_F,
    PROBE_TARGET_STEP_F,
)
from .coordinator import GrillMasterCoordinator
from .temp_unit import bounds_to_display_unit, display_unit, to_display_unit, to_fahrenheit


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Probe 1 Target number entity."""
    coordinator: GrillMasterCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GrillMasterProbe1Target(coordinator, entry)])


class GrillMasterProbe1Target(
    CoordinatorEntity[GrillMasterCoordinator], NumberEntity
):
    """Settable target (done) temperature for meat probe 1.

    Only probe 1 has a target on the LBL control board (LG1000BL) - the
    MCU has no command to set a target for probes 2+.
    """

    _attr_has_entity_name = True
    _attr_name = "Probe 1 Target"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-probe"

    def __init__(
        self,
        coordinator: GrillMasterCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._api: GrillMasterApi = coordinator.api
        self._attr_unique_id = f"{entry.entry_id}_probe1_target"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

        self._attr_native_unit_of_measurement = display_unit(coordinator.hass)
        self._attr_native_min_value, self._attr_native_max_value = (
            bounds_to_display_unit(
                PROBE_TARGET_MIN_F,
                PROBE_TARGET_MAX_F,
                self._attr_native_unit_of_measurement,
            )
        )
        self._attr_native_step = PROBE_TARGET_STEP_F

    @property
    def native_value(self) -> float | None:
        """Return probe 1's currently set target temperature."""
        if self.coordinator.data is None:
            return None
        temp = self.coordinator.data.get("p1_target")
        if not temp or temp <= 0:
            return None
        return to_display_unit(temp, self._attr_native_unit_of_measurement)

    async def async_set_native_value(self, value: float) -> None:
        """Set probe 1's target temperature."""
        temp_f = to_fahrenheit(value, self._attr_native_unit_of_measurement)
        temp_f = int(round(temp_f))
        temp_f = max(PROBE_TARGET_MIN_F, min(PROBE_TARGET_MAX_F, temp_f))

        await self._api.set_probe_1_target(temp_f)
        await self.coordinator.async_request_refresh()
