from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AllpowersBLE, AllpowersBLECoordinator
from .const import DOMAIN
from .models import AllpowersBLEData

PERCENT_REMAIN_DESCRIPTION = SensorEntityDescription(
    key="percent_remain",
    device_class=SensorDeviceClass.BATTERY,
    entity_registry_enabled_default=True,
    entity_registry_visible_default=True,
    has_entity_name=True,
    name="Remaining Charge",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
)

MINUTES_REMAIN_DESCRIPTION = SensorEntityDescription(
    key="minutes_remain",
    device_class=SensorDeviceClass.DURATION,
    entity_registry_enabled_default=True,
    entity_registry_visible_default=True,
    has_entity_name=True,
    name="Remaining Time",
    native_unit_of_measurement=UnitOfTime.MINUTES,
    state_class=SensorStateClass.MEASUREMENT,
)

WATTS_IMPORT_DESCRIPTION = SensorEntityDescription(
    key="watts_import",
    device_class=SensorDeviceClass.POWER,
    entity_registry_enabled_default=True,
    entity_registry_visible_default=True,
    has_entity_name=True,
    name="Battery Watts Import",
    native_unit_of_measurement=UnitOfPower.WATT,
    state_class=SensorStateClass.MEASUREMENT,
)

WATTS_EXPORT_DESCRIPTION = SensorEntityDescription(
    key="watts_export",
    device_class=SensorDeviceClass.POWER,
    entity_registry_enabled_default=True,
    entity_registry_visible_default=True,
    has_entity_name=True,
    name="Battery Watts Export",
    native_unit_of_measurement=UnitOfPower.WATT,
    state_class=SensorStateClass.MEASUREMENT,
)

UPS_STATUS_DESCRIPTION = SensorEntityDescription(
    key="ups_status",
    device_class=SensorDeviceClass.ENUM,
    entity_registry_enabled_default=True,
    entity_registry_visible_default=True,
    has_entity_name=True,
    translation_key="ups_status",
    options=["bypass", "battery", "ac_output_off"],
)

UPS_STATUS_POLL_INTERVAL = timedelta(seconds=5)

SENSOR_DESCRIPTIONS = [
    PERCENT_REMAIN_DESCRIPTION,
    MINUTES_REMAIN_DESCRIPTION,
    WATTS_IMPORT_DESCRIPTION,
    WATTS_EXPORT_DESCRIPTION,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform for Allpowers BLE"""
    data: AllpowersBLEData = hass.data[DOMAIN][entry.entry_id]
    entities = [
        AllpowersBLESensor(
            data.coordinator,
            data.device,
            entry.title,
            description,
        )
        for description in SENSOR_DESCRIPTIONS
    ]
    if data.device.supports_ups_status:
        entities.append(
            AllpowersBLEUpsStatusSensor(
                data.coordinator, data.device, entry.title, UPS_STATUS_DESCRIPTION
            )
        )
    async_add_entities(entities)


class AllpowersBLESensor(
    CoordinatorEntity[AllpowersBLECoordinator], SensorEntity, RestoreEntity
):
    """Generic sensor for Allpowers BLE"""

    def __init__(
        self,
        coordinator: AllpowersBLECoordinator,
        device: AllpowersBLE,
        name: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._device = device
        self._key = description.key
        self.entity_description = description
        self._attr_unique_id = f"{device.address}_{self._key}"
        self._attr_device_info = DeviceInfo(
            name=name,
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if not (last_state := await self.async_get_last_state()):
            return
        self._attr_native_value = last_state.state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator"""
        self._attr_native_value = getattr(self._device, self._key)
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Unavailable if coordinator isn't connected"""
        return True

    @property
    def assumed_state(self) -> bool:
        return not self._coordinator.connected

    @property
    def native_value(self) -> str | int | None:
        return getattr(self._device, self._key)


class AllpowersBLEUpsStatusSensor(AllpowersBLESensor):
    """Read-only UPS status with a periodic status request."""

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._async_update_ups_status, UPS_STATUS_POLL_INTERVAL
            )
        )

    async def _async_update_ups_status(self, _now: datetime) -> None:
        """Update availability even if the station has stopped sending data."""
        self.async_write_ha_state()
        await self._device.async_request_ups_status()

    @property
    def available(self) -> bool:
        return self.native_value is not None

    @property
    def assumed_state(self) -> bool:
        return False
