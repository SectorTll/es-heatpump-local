"""Offline checks of the settings field dictionary (fields.py has no Home Assistant imports)."""
import importlib
import math
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
package = types.ModuleType("fields_under_test")
package.__path__ = [str(ROOT / "custom_components/es_heatpump_local")]
sys.modules[package.__name__] = package
fields = importlib.import_module("fields_under_test.fields")


class FieldDictionaryTests(unittest.TestCase):
    def test_coverage_and_confidence(self):
        labelled = set(fields.SETTINGS_FIELDS)
        unknown = set(fields.UNLABELLED_SETTINGS)
        self.assertEqual(labelled | unknown, set(range(1, 137)))
        self.assertEqual(labelled & unknown, set())
        confidence = [f["confidence"] for f in fields.SETTINGS_FIELDS.values()]
        self.assertEqual(confidence.count("verified"), 72)
        self.assertEqual(confidence.count("unverified"), 56)
        self.assertEqual(len(unknown), 8)
        self.assertEqual(set(confidence), {"verified", "unverified"})

    def test_names_unique_and_ranges_sane(self):
        names = [fields.setting_name(i) for i in range(1, 137)]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(fields.setting_name(55), "DHW main setpoint (par55)")
        self.assertEqual(fields.setting_name(14), "Setting 014")
        for index, field in fields.SETTINGS_FIELDS.items():
            self.assertTrue(field["name"].strip(), index)
            self.assertTrue(all(isinstance(k, int) and isinstance(v, str) and v for k, v in field["options"].items()), index)
            if field["min"] is not None and field["max"] is not None:
                self.assertLessEqual(field["min"], field["max"], index)
            self.assertEqual(field["range_source"] is None, field["min"] is None and field["max"] is None, index)
            self.assertIn(field["range_source"], (None, "form", "list"), index)

    def test_option_label_is_strict(self):
        options = fields.SETTINGS_FIELDS[4]["options"]
        self.assertEqual(fields.option_label(options, 4), "Auto")
        self.assertEqual(fields.option_label(options, 4.0), "Auto")
        self.assertEqual(fields.option_label(options, "4"), "Auto")
        for value in (1.4, 7, -1, None, True, float("nan"), float("inf"), 1e300, "x", object()):
            self.assertIsNone(fields.option_label(options, value), value)
        self.assertIsNone(fields.option_label({}, 1))

    def test_attributes_keep_namespaces_apart(self):
        live = fields.live_portal_attributes(40)
        setting = fields.setting_attributes(38, 35.0)
        self.assertEqual(live, {"portal_realdata_parameter": "par38"})
        self.assertEqual(setting["portal_setdata_parameter"], "par38")
        self.assertNotIn("portal_setdata_parameter", live)
        self.assertEqual(fields.live_portal_attributes(1), {})
        self.assertEqual(fields.live_portal_attributes(2), {})
        self.assertEqual(fields.live_portal_attributes(3), {"portal_realdata_parameter": "par1"})

    def test_setting_attributes(self):
        attrs = fields.setting_attributes(4, 4.0)
        self.assertEqual(attrs["label_confidence"], "verified")
        self.assertEqual(attrs["value_label"], "Auto")
        self.assertEqual(attrs["options"]["4"], "Auto")
        self.assertIn("options_source", attrs)
        self.assertNotIn("value_label", fields.setting_attributes(4, 1.4))
        self.assertNotIn("value_label", fields.setting_attributes(4, math.nan))
        self.assertNotIn("value_label", fields.setting_attributes(4, None))
        unverified = fields.setting_attributes(89, 1.0)
        self.assertEqual(unverified["label_confidence"], "unverified")
        self.assertEqual(unverified["value_label"], "ON Constantly")
        unknown = fields.setting_attributes(14, 60.0)
        self.assertEqual(unknown, {"portal_setdata_parameter": "par14", "label_confidence": "unknown"})
        ranged = fields.setting_attributes(55, 50.0)
        self.assertEqual(ranged["portal_range"], [25, 75])
        self.assertIn("reference installation", ranged["portal_range_source"])


if __name__ == "__main__":
    unittest.main()
