"""Sensor entities for ES Heatpump Local."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
import time

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
    LONG_SENSOR_COUNT,
    SHORT_SENSOR_COUNT,
)
from .coordinator import ESHeatpumpLocalCoordinator
from .fields import live_portal_attributes, setting_attributes, setting_name


@dataclass(frozen=True, kw_only=True)
class HeatpumpLocalSensorDescription(SensorEntityDescription):
    """Describe an ES Heatpump Local sensor."""

    value_key: str
    index: int | None = None
    value_formatter: Callable[[Any], Any] | None = None
    alias: str | None = None
    protocol_label: str | None = None
    installation_note: str | None = None
    label_confidence: str | None = None
    note: str | None = None
    extra_attributes: tuple[tuple[str, Any], ...] = ()


def _coerce_int(value: Any) -> int | None:
    """Convert a pushed numeric value into an integer code."""
    try:
        return int(round(float(value)))
    except (TypeError, ValueError, OverflowError):
        return None


def _format_version_code(value: Any) -> str | None:
    """Format values like 205 into V2.05."""
    code = _coerce_int(value)
    if code is None:
        return None

    major = code // 100
    minor = code % 100
    return f"V{major}.{minor:02d}"


# Live value NN corresponds to myheatpump.com realdata par(NN-2); settings long_NNN to setdata parNNN.
# Keep raw numeric states and unique IDs so existing history/references survive.
PORTAL_MODE_LABELS = {
    0: "standby", 1: "domestic_hot_water", 2: "heating", 3: "cooling",
    4: "domestic_hot_water_and_heating", 5: "domestic_hot_water_and_cooling",
}
PORTAL_MATCHED_INDICES = {3, 35, 36, 37, 38, 40, 43, 44, 45}

# Temperature differences must not use the absolute temperature device class.
TEMPERATURE_DELTA = getattr(SensorDeviceClass, "TEMPERATURE_DELTA", None)
GAUGE_PRESSURE = {"pressure_reference": "gauge (inferred)"}
GAUGE_NOTE = (
    "Saturation temperature at gauge pressure + 1 atm matched outdoor air at standstill "
    "on the reference unit; not a sensor calibration."
)

KNOWN_LIVE_SENSOR_OVERRIDES: dict[int, dict[str, Any]] = {
    3: {
        "name": "Current Working Mode", "icon": "mdi:heat-pump",
        "state_class": SensorStateClass.MEASUREMENT, "label_confidence": "portal-form",
    },
    6: {
        "name": "Heat Exchanger Water Outlet Temp (Tuo)",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-diagram",
    },
    7: {
        "name": "Heat Exchanger Water Return Temp (Tuj)",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-diagram",
    },
    8: {
        "name": "Indoor Coil Temp (Tup)",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-diagram",
    },
    9: {
        "name": "Sanitary Hot Water Temp (TW)",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-form",
    },
    10: {
        "name": "Cooling/Heating Water Temp (TC)",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-form",
    },
    11: {
        "name": "Mixing Valve 1 Water Temp (TV1)",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "protocol_label": "TV1",
        "label_confidence": "portal-form",
    },
    12: {
        "name": "Mixing Valve 2 Water Temp (TV2)",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "protocol_label": "TV2",
        "label_confidence": "portal-form",
    },
    13: {
        "name": "TR1",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "protocol_label": "TR1",
        "label_confidence": "portal-form",
    },
    17: {
        "name": "P0-Correlated Signal (unidentified)", "icon": "mdi:pump",
        "state_class": SensorStateClass.MEASUREMENT, "label_confidence": "inferred",
        "note": (
            "Followed circulation pump P0 (live 35) within about 10 s on the reference unit; "
            "physical meaning not established."
        ),
    },
    22: {
        "name": "Compressor Working Speed",
        "icon": "mdi:engine-outline",
        "device_class": SensorDeviceClass.FREQUENCY,
        "native_unit_of_measurement": UnitOfFrequency.HERTZ,
        "label_confidence": "portal-form",
    },
    23: {
        "name": "EEV Opening",
        "icon": "mdi:valve",
        "native_unit_of_measurement": "steps",
        "label_confidence": "portal-diagram",
    },
    24: {
        "name": "High Pressure (Pd)",
        "icon": "mdi:gauge",
        "device_class": SensorDeviceClass.PRESSURE,
        "native_unit_of_measurement": UnitOfPressure.BAR,
        "label_confidence": "portal-diagram",
        "note": GAUGE_NOTE,
        "extra_attributes": GAUGE_PRESSURE,
    },
    25: {
        "name": "Low Pressure (Ps)",
        "icon": "mdi:gauge-low",
        "device_class": SensorDeviceClass.PRESSURE,
        "native_unit_of_measurement": UnitOfPressure.BAR,
        "label_confidence": "portal-diagram",
        "note": GAUGE_NOTE,
        "extra_attributes": GAUGE_PRESSURE,
    },
    26: {
        "name": "Actual Outdoor Temp (Ta)",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-form",
    },
    27: {
        "name": "Discharge Temp (Td)",
        "icon": "mdi:thermometer-high",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-diagram",
    },
    28: {
        "name": "Suction Temp (Ts)",
        "icon": "mdi:thermometer-low",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-diagram",
    },
    29: {
        "name": "Outdoor Coil Temp (Tp)",
        "icon": "mdi:snowflake-thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-diagram",
        "note": "Named Suction Temp (Ts) before 0.2.0; suction temperature is live 28.",
    },
    30: {
        "name": "Fan Speed 1",
        "icon": "mdi:fan",
        "native_unit_of_measurement": "rpm",
        "label_confidence": "portal-diagram",
    },
    31: {
        "name": "Fan Speed 2",
        "icon": "mdi:fan",
        "native_unit_of_measurement": "rpm",
        "label_confidence": "portal-diagram",
        "note": "Zero on single-fan units; not physically verified.",
    },
    32: {
        "name": "Outdoor Unit Working Current",
        "icon": "mdi:current-ac",
        "device_class": SensorDeviceClass.CURRENT,
        "native_unit_of_measurement": UnitOfElectricCurrent.AMPERE,
        "label_confidence": "portal-diagram",
    },
    33: {
        "name": "Voltage",
        "icon": "mdi:sine-wave",
        "device_class": SensorDeviceClass.VOLTAGE,
        "native_unit_of_measurement": UnitOfElectricPotential.VOLT,
        "label_confidence": "portal-form",
    },
    35: {
        "name": "Circulation Pump P0 Status", "icon": "mdi:pump",
        "state_class": SensorStateClass.MEASUREMENT, "label_confidence": "portal-form",
    },
    36: {
        "name": "Circulation Pump P1 Status", "icon": "mdi:pump",
        "state_class": SensorStateClass.MEASUREMENT, "label_confidence": "portal-form",
    },
    37: {
        "name": "Circulation Pump P2 Status", "icon": "mdi:pump",
        "state_class": SensorStateClass.MEASUREMENT, "label_confidence": "portal-form",
    },
    38: {
        "name": "Active Target Temperature",
        "icon": "mdi:thermostat",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "label_confidence": "portal-form",
    },
    39: {
        "name": "Software Version",
        "icon": "mdi:identifier",
        "state_class": None,
        "value_formatter": _format_version_code,
        "label_confidence": "portal-form",
    },
    40: {
        "name": "Compressor Control Level (inferred)", "icon": "mdi:engine-outline",
        "state_class": SensorStateClass.MEASUREMENT, "label_confidence": "inferred",
        "note": (
            "Portal label Calculated Comp. Speed. Dimensionless 0-10 step, not a frequency; "
            "compressor Hz followed it within 1-2 frames on the reference unit."
        ),
    },
    41: {
        "name": "Suction Superheat (inferred)", "icon": "mdi:thermometer-lines",
        "device_class": TEMPERATURE_DELTA,
        "native_unit_of_measurement": UnitOfTemperature.KELVIN,
        "label_confidence": "inferred",
        "note": (
            "Controller-reported packet value. Matched Ts - Tsat(Ps + 1 bar) within about "
            "0.1-0.3 K on the reference R410A unit."
        ),
    },
    42: {
        "name": "Discharge Superheat (inferred)", "icon": "mdi:thermometer-lines",
        "device_class": TEMPERATURE_DELTA,
        "native_unit_of_measurement": UnitOfTemperature.KELVIN,
        "label_confidence": "inferred",
        "note": (
            "Controller-reported packet value. Matched Td - Tsat(Pd + 1 bar) within about "
            "0.2-0.3 K on the reference R410A unit."
        ),
    },
    43: {
        "name": "Auxiliary Heater AH Working Time", "icon": "mdi:timer-outline",
        "device_class": SensorDeviceClass.DURATION,
        "native_unit_of_measurement": UnitOfTime.MINUTES,
        "state_class": SensorStateClass.MEASUREMENT, "label_confidence": "portal-form",
    },
    44: {
        "name": "Heating Backup Heater HBH Working Time", "icon": "mdi:timer-outline",
        "device_class": SensorDeviceClass.DURATION,
        "native_unit_of_measurement": UnitOfTime.MINUTES,
        "state_class": SensorStateClass.MEASUREMENT, "label_confidence": "portal-form",
    },
    45: {
        "name": "Hot Water Backup Heater HWTBH Working Time", "icon": "mdi:timer-outline",
        "device_class": SensorDeviceClass.DURATION,
        "native_unit_of_measurement": UnitOfTime.MINUTES,
        "state_class": SensorStateClass.MEASUREMENT, "label_confidence": "portal-form",
    },
}


META_SENSORS: tuple[HeatpumpLocalSensorDescription, ...] = (
    HeatpumpLocalSensorDescription(
        key="connected_clients",
        value_key="connected_clients",
        name="Connected Clients",
        icon="mdi:lan-connect",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HeatpumpLocalSensorDescription(
        key="frames_received",
        value_key="frames_received",
        name="Frames Received",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    HeatpumpLocalSensorDescription(
        key="short_frames_received",
        value_key="short_frames_received",
        name="Short Frames Received",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    HeatpumpLocalSensorDescription(
        key="long_frames_received",
        value_key="long_frames_received",
        name="Long Frames Received",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    HeatpumpLocalSensorDescription(
        key="last_frame_type",
        value_key="last_frame_type",
        name="Last Frame Type",
        icon="mdi:shape-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    HeatpumpLocalSensorDescription(
        key="last_frame_at",
        value_key="last_frame_at",
        name="Last Frame At",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-outline",
    ),
    HeatpumpLocalSensorDescription(
        key="last_checksum",
        value_key="last_checksum",
        name="Last Checksum",
        icon="mdi:checksum",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


def _live_description(idx: int) -> HeatpumpLocalSensorDescription:
    """Build the description of one live-frame value from its override, if any."""
    override = KNOWN_LIVE_SENSOR_OVERRIDES.get(idx, {})
    return HeatpumpLocalSensorDescription(
        key=f"short_{idx:02d}",
        value_key=f"short_{idx:02d}",
        name=override.get("name", f"Live {idx:02d}"),
        icon=override.get("icon", "mdi:gauge"),
        index=idx,
        alias=override.get("alias"),
        protocol_label=override.get("protocol_label"),
        installation_note=override.get("installation_note"),
        device_class=override.get("device_class"),
        native_unit_of_measurement=override.get("native_unit_of_measurement"),
        state_class=override.get("state_class", SensorStateClass.MEASUREMENT),
        value_formatter=override.get("value_formatter"),
        label_confidence=override.get("label_confidence", "unknown"),
        note=override.get("note"),
        extra_attributes=tuple(override.get("extra_attributes", {}).items()),
    )


LIVE_SENSORS: tuple[HeatpumpLocalSensorDescription, ...] = tuple(
    _live_description(idx) for idx in range(1, SHORT_SENSOR_COUNT + 1)
)

NAMED_SETTINGS_SENSORS: tuple[HeatpumpLocalSensorDescription, ...] = (
    HeatpumpLocalSensorDescription(
        key="hot_water_target_temperature",
        value_key="long_055",
        name="Hot Water Base Target Temperature",
        icon="mdi:water-thermometer",
        index=55,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HeatpumpLocalSensorDescription(
        # Key kept from 0.1.0 ("daytime") so the unique ID and entity ID do not change.
        key="hot_water_daytime_target_temperature",
        value_key="long_065",
        name="Hot Water Reheating Target Temperature",
        icon="mdi:water-thermometer-outline",
        index=65,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

SETTINGS_SENSORS: tuple[HeatpumpLocalSensorDescription, ...] = tuple(
    HeatpumpLocalSensorDescription(
        key=f"long_{idx:03d}",
        value_key=f"long_{idx:03d}",
        name=setting_name(idx),
        icon="mdi:tune-variant",
        index=idx,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    )
    for idx in range(1, LONG_SENSOR_COUNT + 1)
)

ALL_SENSORS = META_SENSORS + LIVE_SENSORS + NAMED_SETTINGS_SENSORS + SETTINGS_SENSORS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: ESHeatpumpLocalCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=DEVICE_NAME,
        manufacturer=DEVICE_MANUFACTURER,
        model=DEVICE_MODEL,
    )

    async_add_entities(
        ESHeatpumpLocalSensor(
            coordinator=coordinator,
            device_info=device_info,
            description=description,
        )
        for description in ALL_SENSORS
    )


class ESHeatpumpLocalSensor(CoordinatorEntity[ESHeatpumpLocalCoordinator], SensorEntity):
    """Represent one pushed heat pump value."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_force_update = False

    entity_description: HeatpumpLocalSensorDescription

    def __init__(
        self,
        coordinator: ESHeatpumpLocalCoordinator,
        device_info: DeviceInfo,
        description: HeatpumpLocalSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{coordinator.port}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        """Return the current value from the pushed frame data."""
        value = self.coordinator.data.get(self.entity_description.value_key)
        formatter = self.entity_description.value_formatter
        if formatter is None:
            return value

        return formatter(value)

    @property
    def available(self) -> bool:
        """Mark the sensor unavailable until its first value arrives."""
        if self.entity_description.key in {
            "connected_clients",
            "frames_received",
            "short_frames_received",
            "long_frames_received",
            "last_frame_type",
            "last_frame_at",
            "last_checksum",
        }:
            return True

        return self.entity_description.value_key in self.coordinator.data

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose raw index and field metadata for easier reverse-engineering."""
        description = self.entity_description
        if description.key == "connected_clients":
            return {"channels": [
                {"peer": str(w.get_extra_info("peername")),
                 "verified_packet_age_seconds": round(time.monotonic() - c.updated, 1) if c.latest is not None else None,
                 "fresh_verified": c.latest is not None and not w.is_closing() and time.monotonic() - c.updated <= 90}
                for w, c in self.coordinator._channels.items()]}
        if description.index is None:
            return {}

        index = description.index
        attrs: dict[str, Any] = {"raw_index": index}

        if description.value_key.startswith("short_"):
            if index in PORTAL_MATCHED_INDICES:
                attrs["portal_parameter"] = f"par{index - 2}"  # 0.1.0 attribute, kept
            attrs.update(live_portal_attributes(index))
            attrs["label_confidence"] = description.label_confidence or "unknown"
            if index == 3:
                attrs["working_mode"] = PORTAL_MODE_LABELS.get(
                    _coerce_int(self.native_value), "unknown"
                )
            elif index in {35, 36, 37}:
                attrs["pump_status"] = {0: "off", 1: "on"}.get(
                    _coerce_int(self.native_value), "unknown"
                )
                attrs["status_source"] = "heatpump_controller"
        else:
            attrs.update(
                setting_attributes(index, self.coordinator.data.get(description.value_key))
            )

        if description.note:
            attrs["note"] = description.note
        attrs.update(dict(description.extra_attributes))
        if description.protocol_label:
            attrs["protocol_label"] = description.protocol_label
        if description.alias:
            attrs["alias"] = description.alias
        if description.installation_note:
            attrs["installation_note"] = description.installation_note

        return attrs
