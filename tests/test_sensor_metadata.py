"""Offline checks that sensor descriptions keep their keys and expose the new metadata as attributes."""
import math
import unittest

from ha_stubs import FakeCoordinator, load_sensor_module

sensor = load_sensor_module("sensor_under_test")

META_KEYS = ["connected_clients", "frames_received", "short_frames_received", "long_frames_received",
             "last_frame_type", "last_frame_at", "last_checksum"]
EXPECTED_KEYS = (META_KEYS + [f"short_{i:02d}" for i in range(1, 46)]
                 + ["hot_water_target_temperature", "hot_water_daytime_target_temperature"]
                 + [f"long_{i:03d}" for i in range(1, 137)])


def entity(key, data=None):
    description = next(d for d in sensor.ALL_SENSORS if d.key == key)
    return sensor.ESHeatpumpLocalSensor(FakeCoordinator(data), {}, description)


class SensorMetadataTests(unittest.TestCase):
    def test_keys_value_keys_and_unique_ids_unchanged(self):
        keys = [d.key for d in sensor.ALL_SENSORS]
        self.assertEqual(keys, EXPECTED_KEYS)
        for d in sensor.ALL_SENSORS:
            if d.key.startswith(("short_", "long_")):
                self.assertEqual(d.value_key, d.key)
        named = {d.key: d.value_key for d in sensor.NAMED_SETTINGS_SENSORS}
        self.assertEqual(named, {"hot_water_target_temperature": "long_055",
                                 "hot_water_daytime_target_temperature": "long_065"})
        ids = [entity(k)._attr_unique_id for k in keys]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("es_heatpump_local_18899_short_29", ids)
        self.assertIn("es_heatpump_local_18899_hot_water_daytime_target_temperature", ids)

    def test_names_units_and_classes(self):
        d = {x.key: x for x in sensor.ALL_SENSORS}
        cls = sensor.SensorDeviceClass
        self.assertEqual(d["short_28"].name, "Suction Temp (Ts)")
        self.assertEqual(d["short_28"].native_unit_of_measurement, "°C")
        self.assertEqual(d["short_28"].device_class, cls.TEMPERATURE)
        self.assertEqual(d["short_29"].name, "Outdoor Coil Temp (Tp)")
        self.assertEqual(d["short_31"].name, "Fan Speed 2")
        self.assertEqual(d["short_31"].native_unit_of_measurement, "rpm")
        self.assertEqual(d["short_40"].name, "Compressor Control Level (inferred)")
        self.assertIsNone(d["short_40"].native_unit_of_measurement)
        self.assertEqual(d["short_17"].name, "P0-Correlated Signal (unidentified)")
        for key in ("short_41", "short_42"):
            self.assertEqual(d[key].native_unit_of_measurement, "K")
            self.assertEqual(d[key].device_class, cls.TEMPERATURE_DELTA)
            self.assertNotEqual(d[key].device_class, cls.TEMPERATURE)
        self.assertEqual(d["hot_water_daytime_target_temperature"].name, "Hot Water Reheating Target Temperature")
        self.assertEqual(d["long_055"].name, "DHW main setpoint (par55)")
        self.assertEqual(d["long_014"].name, "Setting 014")
        self.assertEqual(d["short_06"].name, "Heat Exchanger Water Outlet Temp (Tuo)")
        self.assertEqual(d["short_05"].name, "Live 05")
        hash(d["short_24"])  # descriptions must stay hashable

    def test_fallback_without_temperature_delta(self):
        old = load_sensor_module("sensor_old_ha", with_temperature_delta=False)
        d = {x.key: x for x in old.ALL_SENSORS}
        for key in ("short_41", "short_42"):
            self.assertIsNone(d[key].device_class)
            self.assertEqual(d[key].native_unit_of_measurement, "K")

    def test_live_attributes(self):
        attrs = entity("short_24", {"short_24": 11.8}).extra_state_attributes
        self.assertEqual(attrs["pressure_reference"], "gauge (inferred)")
        self.assertEqual(attrs["label_confidence"], "portal-diagram")
        self.assertEqual(attrs["portal_realdata_parameter"], "par22")
        self.assertIn("gauge pressure", attrs["note"])
        self.assertEqual(attrs["raw_index"], 24)
        self.assertIn("not a frequency", entity("short_40").extra_state_attributes["note"])
        unknown = entity("short_05").extra_state_attributes
        self.assertEqual(unknown["label_confidence"], "unknown")
        self.assertEqual(unknown["portal_realdata_parameter"], "par3")
        self.assertNotIn("portal_realdata_parameter", entity("short_01").extra_state_attributes)
        self.assertEqual(entity("short_38").extra_state_attributes["portal_parameter"], "par36")

    def test_mode_and_pump_labels_do_not_crash(self):
        for value in (float("inf"), float("nan"), None):
            attrs = entity("short_03", {"short_03": value}).extra_state_attributes
            self.assertEqual(attrs["working_mode"], "unknown")
        self.assertEqual(entity("short_03", {"short_03": 2.0}).extra_state_attributes["working_mode"], "heating")
        self.assertEqual(entity("short_35", {"short_35": 1.0}).extra_state_attributes["pump_status"], "on")
        self.assertIsNone(entity("short_39", {"short_39": float("inf")}).native_value)
        self.assertEqual(entity("short_39", {"short_39": 205.0}).native_value, "V2.05")

    def test_setting_attributes_and_raw_values(self):
        e = entity("long_004", {"long_004": 1.4})
        self.assertEqual(e.native_value, 1.4)
        attrs = e.extra_state_attributes
        self.assertEqual(attrs["portal_setdata_parameter"], "par4")
        self.assertEqual(attrs["label_confidence"], "verified")
        self.assertNotIn("value_label", attrs)
        self.assertEqual(entity("long_004", {"long_004": 4.0}).extra_state_attributes["value_label"], "Auto")
        for value in (math.nan, math.inf, None):
            self.assertNotIn("value_label", entity("long_004", {"long_004": value}).extra_state_attributes)
        self.assertEqual(entity("long_014", {"long_014": 60.0}).extra_state_attributes["label_confidence"], "unknown")
        alias = entity("hot_water_daytime_target_temperature", {"long_065": 45.0}).extra_state_attributes
        self.assertEqual(alias["portal_setdata_parameter"], "par65")
        self.assertEqual(alias["label_confidence"], "verified")


if __name__ == "__main__":
    unittest.main()
