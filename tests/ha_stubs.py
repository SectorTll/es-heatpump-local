"""Minimal Home Assistant stand-ins so sensor.py can be imported offline (CI has no Home Assistant).

Only the names sensor.py uses are provided. `load_sensor_module` imports the integration's sensor.py
under a throw-away package name, with a fake coordinator module, optionally without
SensorDeviceClass.TEMPERATURE_DELTA (older Home Assistant releases).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import enum
import importlib
from pathlib import Path
import sys
import types
from typing import Any

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "es_heatpump_local"


def _module(name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


def install_homeassistant(with_temperature_delta: bool = True) -> None:
    for name in [n for n in sys.modules if n == "homeassistant" or n.startswith("homeassistant.")]:
        del sys.modules[name]
    _module("homeassistant")
    _module("homeassistant.components")
    sensor = _module("homeassistant.components.sensor")
    members = {"TEMPERATURE": "temperature", "PRESSURE": "pressure", "FREQUENCY": "frequency",
               "CURRENT": "current", "VOLTAGE": "voltage", "DURATION": "duration", "TIMESTAMP": "timestamp"}
    if with_temperature_delta:
        members["TEMPERATURE_DELTA"] = "temperature_delta"
    sensor.SensorDeviceClass = enum.Enum("SensorDeviceClass", members, type=str)
    sensor.SensorStateClass = enum.Enum(
        "SensorStateClass", {"MEASUREMENT": "measurement", "TOTAL": "total", "TOTAL_INCREASING": "total_increasing"},
        type=str)

    @dataclass(frozen=True, kw_only=True)
    class SensorEntityDescription:
        key: str
        name: str | None = None
        icon: str | None = None
        device_class: Any = None
        native_unit_of_measurement: str | None = None
        state_class: Any = None
        entity_category: Any = None
        entity_registry_enabled_default: bool = True

    class SensorEntity:
        pass

    sensor.SensorEntityDescription = SensorEntityDescription
    sensor.SensorEntity = SensorEntity

    _module("homeassistant.config_entries").ConfigEntry = type("ConfigEntry", (), {})
    const = _module("homeassistant.const")
    const.EntityCategory = enum.Enum("EntityCategory", {"CONFIG": "config", "DIAGNOSTIC": "diagnostic"}, type=str)
    const.PERCENTAGE = "%"
    const.UnitOfElectricCurrent = types.SimpleNamespace(AMPERE="A")
    const.UnitOfElectricPotential = types.SimpleNamespace(VOLT="V")
    const.UnitOfFrequency = types.SimpleNamespace(HERTZ="Hz")
    const.UnitOfPressure = types.SimpleNamespace(BAR="bar")
    const.UnitOfTemperature = types.SimpleNamespace(CELSIUS="°C", KELVIN="K")
    const.UnitOfTime = types.SimpleNamespace(MINUTES="min")
    _module("homeassistant.core").HomeAssistant = type("HomeAssistant", (), {})
    _module("homeassistant.helpers")
    _module("homeassistant.helpers.device_registry").DeviceInfo = dict
    _module("homeassistant.helpers.entity_platform").AddEntitiesCallback = object

    class CoordinatorEntity:
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, coordinator):
            self.coordinator = coordinator

    class DataUpdateCoordinator:
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, hass, logger, name=None, **kwargs):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.data = None
            self.updates = []

        def async_set_updated_data(self, data):
            self.data = data
            self.updates.append(data)

    update_coordinator = _module("homeassistant.helpers.update_coordinator")
    update_coordinator.CoordinatorEntity = CoordinatorEntity
    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    _module("homeassistant.util")
    dt_module = _module("homeassistant.util.dt")
    dt_module.utcnow = lambda: datetime.now(timezone.utc)
    sys.modules["homeassistant.util"].dt = dt_module


def load_coordinator_module(package: str) -> types.ModuleType:
    """Import coordinator.py with the real const/parser/commands modules and stubbed Home Assistant."""
    install_homeassistant()
    for name in [n for n in sys.modules if n == package or n.startswith(package + ".")]:
        del sys.modules[name]
    pkg = types.ModuleType(package)
    pkg.__path__ = [str(COMPONENT)]
    sys.modules[package] = pkg
    return importlib.import_module(f"{package}.coordinator")


def load_sensor_module(package: str, with_temperature_delta: bool = True) -> types.ModuleType:
    """Import sensor.py (and fields.py/const.py) of the integration under a fresh package name."""
    install_homeassistant(with_temperature_delta)
    for name in [n for n in sys.modules if n == package or n.startswith(package + ".")]:
        del sys.modules[name]
    pkg = types.ModuleType(package)
    pkg.__path__ = [str(COMPONENT)]
    sys.modules[package] = pkg
    fake_coordinator = _module(f"{package}.coordinator")
    fake_coordinator.ESHeatpumpLocalCoordinator = type("ESHeatpumpLocalCoordinator", (), {})
    return importlib.import_module(f"{package}.sensor")


class FakeCoordinator:
    """Coordinator stand-in: pushed values in `data`, TCP port for unique IDs."""

    def __init__(self, data: dict[str, Any] | None = None, port: int = 18899) -> None:
        self.data = data or {}
        self.port = port
        self._channels: dict = {}
