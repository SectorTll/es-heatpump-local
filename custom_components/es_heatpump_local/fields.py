"""Field metadata for ES Heatpump Local. Pure Python: no Home Assistant imports.

Two portal namespaces (they reuse the same parN names with different meanings):
  live frame     short_NN  <-> myheatpump.com realdata par(NN-2), NN = 3..45 (address mapping)
  settings frame long_NNN  <-> myheatpump.com setdata  parNNN,   NNN = 1..136

Settings label_confidence:
  verified   - setdata form label; the portal values matched the local settings frame on the reference
               installation (72 fields, 2026-09-12). This verifies the label/index mapping, not every
               option value, range or write safety.
  unverified - label from the myheatpump.com portal parameter list; not yet checked on a real installation.
  unknown    - no label (8 fields).
Options and ranges are portal reference metadata, never validators for commands.
"""
from __future__ import annotations

import math
from typing import Any

LIVE_PORTAL_OFFSET = 2
RANGE_SOURCES = {
    "form": "setdata form of the reference installation (2026-09-12)",
    "list": "portal parameter list (unverified)",
}
OPTIONS_SOURCE = "portal parameter list (unverified)"

# Generated table: {long index: {name, portal_label, confidence, min, max, range_source, options}}
SETTINGS_FIELDS: dict[int, dict[str, Any]] = {
    1: {"name": 'Unit ON/OFF', "portal_label": 'Unit ON OFF', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    2: {"name": 'Software version', "portal_label": 'Software Version No.', "confidence": 'verified', "min": 0, "max": 1000, "range_source": 'form', "options": {}},
    3: {"name": 'Database version', "portal_label": 'Database Version', "confidence": 'verified', "min": 0, "max": 100, "range_source": 'form', "options": {}},
    4: {"name": 'Configured working mode', "portal_label": 'Working Mode', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'Standby', 1: 'Heating', 2: 'Cooling', 3: 'Sanitary Hot Water', 4: 'Auto'}},
    5: {"name": 'Language', "portal_label": 'Language', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'English', 1: 'Slovenščina', 2: 'Deutsch', 3: 'Polski', 4: 'Italiano', 5: 'Русский', 6: 'Українська', 7: 'Polski', 8: 'English', 9: 'English', 10: 'English', 11: 'English', 12: 'English', 13: 'English', 14: 'English', 15: '中文'}},
    6: {"name": 'Sanitary Hot Water', "portal_label": 'Sanitary Hot Water', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    7: {"name": 'Heating', "portal_label": 'Heating', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    8: {"name": 'Cooling', "portal_label": 'Cooling', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    9: {"name": 'Heating/cooling switch source', "portal_label": 'Cooling and Heating Switch', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'Invalid', 1: 'Ambient Temp.', 2: 'External Signal Control', 3: 'External Signal Control+Ambient Temp.'}},
    10: {"name": 'Basic Operation Modes', "portal_label": 'Basic Operation Modes', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    11: {"name": 'Ambient temperature to start heating', "portal_label": 'Ambient Temp. To Start Heating', "confidence": 'verified', "min": -10, "max": 25, "range_source": 'form', "options": {}},
    12: {"name": 'Ambient temperature to start cooling', "portal_label": 'Ambient Temp. To Start Cooling', "confidence": 'verified', "min": 8, "max": 53, "range_source": 'form', "options": {}},
    13: {"name": 'Max Allowed Duration For Min Compressor Speed', "portal_label": 'Max Allowed Duration For Min Compressor Speed', "confidence": 'unverified', "min": 5, "max": 60, "range_source": 'list', "options": {}},
    19: {"name": 'Heating/cooling timer enabled', "portal_label": 'Heating/Cooling ON/OFF Timer', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    20: {"name": 'Heating/cooling stop delta T', "portal_label": 'Heating/Cooling Stops Based on Water ∆T', "confidence": 'verified', "min": 1, "max": 3, "range_source": 'form', "options": {}},
    21: {"name": 'Heating/cooling restart delta T', "portal_label": 'Heating/Cooling Restarts Based on Water ∆T', "confidence": 'verified', "min": 1, "max": 10, "range_source": 'form', "options": {}},
    22: {"name": 'Compressor speed reduction delta T', "portal_label": '∆T Compressor Speed-reduction', "confidence": 'verified', "min": 1, "max": 10, "range_source": 'form', "options": {}},
    23: {"name": 'Cooling setpoint circuit 1', "portal_label": 'Set temp. for Cooling', "confidence": 'verified', "min": 0, "max": 100, "range_source": 'form', "options": {}},
    24: {"name": 'Heating curve circuit 1 enabled', "portal_label": 'Heating Curve', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    25: {"name": 'Curve 1 ambient point A', "portal_label": 'Ambient Temp. 1', "confidence": 'verified', "min": -25, "max": 35, "range_source": 'form', "options": {}},
    26: {"name": 'Curve 1 ambient point B', "portal_label": 'Ambient Temp. 2', "confidence": 'verified', "min": -25, "max": 35, "range_source": 'form', "options": {}},
    27: {"name": 'Curve 1 ambient point C', "portal_label": 'Ambient Temp. 3', "confidence": 'verified', "min": -25, "max": 35, "range_source": 'form', "options": {}},
    28: {"name": 'Curve 1 ambient point D', "portal_label": 'Ambient Temp. 4', "confidence": 'verified', "min": -25, "max": 35, "range_source": 'form', "options": {}},
    29: {"name": 'Curve 1 ambient point E', "portal_label": 'Ambient Temp. 5', "confidence": 'verified', "min": -25, "max": 35, "range_source": 'form', "options": {}},
    30: {"name": 'Curve 1 water point A', "portal_label": 'Water Temp. A /Ambient Temp. 1', "confidence": 'verified', "min": 20, "max": 60, "range_source": 'form', "options": {}},
    31: {"name": 'Curve 1 water point B', "portal_label": 'Water Temp. B/Ambient Temp. 2', "confidence": 'verified', "min": 20, "max": 60, "range_source": 'form', "options": {}},
    32: {"name": 'Curve 1 water point C', "portal_label": 'Water Temp. C/Ambient Temp. 3', "confidence": 'verified', "min": 20, "max": 60, "range_source": 'form', "options": {}},
    33: {"name": 'Curve 1 water point D', "portal_label": 'Water Temp. D/Ambient Temp .4', "confidence": 'verified', "min": 20, "max": 60, "range_source": 'form', "options": {}},
    34: {"name": 'Curve 1 water point E', "portal_label": 'Water Temp. E/Ambient Temp. 5', "confidence": 'verified', "min": 20, "max": 60, "range_source": 'form', "options": {}},
    35: {"name": 'Room temperature effect on heating curve', "portal_label": 'Room temp. effect on Heating Curve', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    36: {"name": 'Ideal room temperature heating', "portal_label": 'Ideal Room temp. in Heating', "confidence": 'verified', "min": 15, "max": 35, "range_source": 'form', "options": {}},
    37: {"name": 'Ideal room temperature cooling', "portal_label": 'Ideal Room temp. in Cooling', "confidence": 'verified', "min": 15, "max": 35, "range_source": 'form', "options": {}},
    38: {"name": 'Fixed heating setpoint circuit 1', "portal_label": 'Set temp. for Heating (without heating curve)', "confidence": 'verified', "min": 20, "max": 60, "range_source": 'form', "options": {}},
    39: {"name": 'Low Temperature Limit', "portal_label": 'Low Temperature Limit', "confidence": 'unverified', "min": 7, "max": 60, "range_source": 'list', "options": {}},
    40: {"name": 'High Temperature Limit', "portal_label": 'High Temperature Limit', "confidence": 'unverified', "min": 7, "max": 75, "range_source": 'list', "options": {}},
    41: {"name": 'Anti-legionella program enabled', "portal_label": 'Anti-Legionella Program', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    42: {"name": 'Anti-legionella setpoint', "portal_label": 'Setpoint', "confidence": 'verified', "min": 60, "max": 80, "range_source": 'form', "options": {}},
    43: {"name": 'Anti-legionella duration', "portal_label": 'Duration', "confidence": 'verified', "min": 5, "max": 60, "range_source": 'form', "options": {}},
    44: {"name": 'Anti-legionella finish time', "portal_label": 'Finish Time', "confidence": 'verified', "min": 10, "max": 180, "range_source": 'form', "options": {}},
    45: {"name": 'Vacation mode enabled', "portal_label": 'Vacation Mode', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    46: {"name": 'Vacation DHW temperature drop', "portal_label": 'Sanitary Hot Water temp. Drop during Vacation Mode', "confidence": 'verified', "min": 10, "max": 50, "range_source": 'form', "options": {}},
    47: {"name": 'Vacation heating water temperature drop', "portal_label": 'Heating Water temp. Drop during Vacation Mode', "confidence": 'verified', "min": 10, "max": 50, "range_source": 'form', "options": {}},
    48: {"name": 'Heating backup source enabled', "portal_label": 'Backup Heating Sources For Heating', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    49: {"name": 'HBH priority relative to AH', "portal_label": 'Priority for Backup Heating Sources (HBH)', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'Lower than AH', 1: 'Higher than AH'}},
    50: {"name": 'DHW backup source enabled', "portal_label": 'Backup Heating Source for Sanitary Hot Water', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    51: {"name": 'HWTBH priority relative to AH', "portal_label": 'Priority for Backup Heating Sources (HWTBH)', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'Lower than AH', 1: 'Higher than AH'}},
    52: {"name": 'HBH accumulating threshold', "portal_label": 'Heating Source Start Accumulating Value (HBH)', "confidence": 'verified', "min": 5, "max": 600, "range_source": 'form', "options": {}},
    53: {"name": 'HWTBH water temperature reading interval', "portal_label": 'Water Temperature Rise Reading Interval (HWTBH)', "confidence": 'verified', "min": 5, "max": 180, "range_source": 'form', "options": {}},
    54: {"name": 'Emergency Operation', "portal_label": 'Emergency Operation', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    55: {"name": 'DHW main setpoint', "portal_label": 'Setpoint DHW', "confidence": 'verified', "min": 25, "max": 75, "range_source": 'form', "options": {}},
    56: {"name": 'DHW main restart delta T', "portal_label": 'DHW Restart ∆T Setting', "confidence": 'verified', "min": 2, "max": 15, "range_source": 'form', "options": {}},
    57: {"name": 'Priority shifting enabled', "portal_label": 'Shifting Priority', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    58: {"name": 'Priority shifting starting temperature', "portal_label": 'Shifting Priority Stating Temp.', "confidence": 'verified', "min": -15, "max": 20, "range_source": 'form', "options": {}},
    59: {"name": 'Minimum DHW working time', "portal_label": 'Sanitary Water Min. Working Hours', "confidence": 'verified', "min": 10, "max": 60, "range_source": 'form', "options": {}},
    60: {"name": 'Maximum heating working time', "portal_label": 'Heating Max. Working Hours', "confidence": 'verified', "min": 30, "max": 180, "range_source": 'form', "options": {}},
    61: {"name": 'Allowable heating temperature drift', "portal_label": 'Allowable temp Drift in Heating', "confidence": 'verified', "min": 3, "max": 10, "range_source": 'form', "options": {}},
    62: {"name": 'DHW backup heater for priority shifting', "portal_label": 'DHW Backup Heater for Shifting Priority', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    63: {"name": 'DHW storage function enabled', "portal_label": 'Sanitary Hot Water Storage Function', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    64: {"name": 'DHW reheating enabled', "portal_label": 'Reheating Function', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    65: {"name": 'DHW reheating setpoint', "portal_label": 'Reheating Set Temp.', "confidence": 'verified', "min": 25, "max": 55, "range_source": 'form', "options": {}},
    66: {"name": 'DHW reheating restart delta T', "portal_label": 'Reheating Restart ∆T Setting', "confidence": 'verified', "min": 2, "max": 20, "range_source": 'form', "options": {}},
    67: {"name": 'Circuit 2 enabled', "portal_label": 'Heating&cooling Circuit 2', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    68: {"name": 'Cooling setpoint circuit 2', "portal_label": 'Set temp. For Cooling', "confidence": 'verified', "min": 0, "max": 100, "range_source": 'form', "options": {}},
    69: {"name": 'Heating curve circuit 2 enabled', "portal_label": 'Heating Curve', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    70: {"name": 'Curve 2 water point A', "portal_label": 'Water Temp. A/Ambient Temp. 1', "confidence": 'verified', "min": -666, "max": 666, "range_source": 'form', "options": {}},
    71: {"name": 'Curve 2 water point B', "portal_label": 'Water Temp. B/Ambient Temp. 2', "confidence": 'verified', "min": -666, "max": 666, "range_source": 'form', "options": {}},
    72: {"name": 'Curve 2 water point C', "portal_label": 'Water Temp. C/Ambient Temp. 3', "confidence": 'verified', "min": -666, "max": 666, "range_source": 'form', "options": {}},
    73: {"name": 'Curve 2 water point D', "portal_label": 'Water Temp. D/Ambient Temp .4', "confidence": 'verified', "min": -666, "max": 666, "range_source": 'form', "options": {}},
    74: {"name": 'Curve 2 water point E', "portal_label": 'Water Temp. E/Ambient Temp. 5', "confidence": 'verified', "min": -666, "max": 666, "range_source": 'form', "options": {}},
    75: {"name": 'Fixed heating setpoint circuit 2', "portal_label": 'Set Temp. for Heating (without heating curve)', "confidence": 'verified', "min": 0, "max": 100, "range_source": 'form', "options": {}},
    76: {"name": 'High Temperature Limit', "portal_label": 'High Temperature Limit', "confidence": 'unverified', "min": 7, "max": 75, "range_source": 'list', "options": {}},
    77: {"name": 'Low Temperature Limit', "portal_label": 'Low Temperature Limit', "confidence": 'unverified', "min": 7, "max": 60, "range_source": 'list', "options": {}},
    78: {"name": 'Reduced setpoint enabled', "portal_label": 'Reduced Setpoint', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    79: {"name": 'Reduced setpoint temperature offset', "portal_label": 'Temp. Drop/Rise', "confidence": 'verified', "min": 2, "max": 10, "range_source": 'form', "options": {}},
    80: {"name": 'Quiet operation enabled', "portal_label": 'Quiet Operation', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    81: {"name": 'Quiet operation allowable temperature drift', "portal_label": 'Allowable Temp. Drifting', "confidence": 'verified', "min": 2, "max": 10, "range_source": 'form', "options": {}},
    82: {"name": 'Operation Signal for Electrical Utility Lock', "portal_label": 'Operation Signal for Electrical Utility Lock', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'Normally Close', 1: 'Normally Open'}},
    83: {"name": 'Utility lock enabled', "portal_label": 'Electrical Utility Lock', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    84: {"name": 'HBH during utility lock', "portal_label": 'HBH During Electrical Utility Lock', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    85: {"name": 'P0 during utility lock', "portal_label": 'P0 during Electrical Utility Lock', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    86: {"name": 'Panel backlight timeout', "portal_label": 'Control Panel Backlight Light', "confidence": 'verified', "min": None, "max": None, "range_source": None, "options": {0: 'Allways ON', 1: '3 min.', 2: '5 min.', 3: '10 min.'}},
    87: {"name": 'Circulation Pump P0 Type', "portal_label": 'Circulation Pump P0 Type', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'DC Variable Speed Pump (PWM control)', 1: 'AC Pump'}},
    88: {"name": 'Speed Setting of Circulation Pump P0', "portal_label": 'Speed Setting of Circulation Pump P0', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'High Speed', 1: 'Medium Speed', 2: 'Low Speed'}},
    89: {"name": 'Working Mode of Circulation Pump P0', "portal_label": 'Working Mode of Circulation Pump P0', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'Interval working mode', 1: 'ON Constantly', 2: 'OFF with Compressor'}},
    90: {"name": 'Pump Off Interval for P0', "portal_label": 'Pump Off Interval for P0', "confidence": 'unverified', "min": 5, "max": 60, "range_source": 'list', "options": {}},
    91: {"name": 'Pump On Time for P0', "portal_label": 'Pump On Time for P0', "confidence": 'unverified', "min": 1, "max": 10, "range_source": 'list', "options": {}},
    92: {"name": 'Buffer Tank', "portal_label": 'Buffer Tank', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    93: {"name": 'Mixing Valve', "portal_label": 'Mixing Valve', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    94: {"name": 'Mixing Valve', "portal_label": 'Mixing Valve', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    95: {"name": 'P1 for Heating Operation', "portal_label": 'P1 for Heating Operation', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    96: {"name": 'P1 for Cooling Operation', "portal_label": 'P1 for Cooling Operation', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    97: {"name": 'P1 with High Temp. Demand', "portal_label": 'P1 with High Temp. Demand', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    98: {"name": 'P2 for Heating Operation', "portal_label": 'P2 for Heating Operation', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    99: {"name": 'P2 for Cooling Operation', "portal_label": 'P2 for Cooling Operation', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    100: {"name": 'P2 with High Temp. Demand', "portal_label": 'P2 with High Temp. Demand', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    101: {"name": 'Floor Curing', "portal_label": 'Floor Curing', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    102: {"name": 'Floor Curing Current Stage', "portal_label": 'Floor Curing Current Stage', "confidence": 'unverified', "min": 0, "max": 16, "range_source": 'list', "options": {}},
    103: {"name": 'Floor Curing Current Stage Running Duration', "portal_label": 'Floor Curing Current Stage Running Duration', "confidence": 'unverified', "min": -50, "max": 500, "range_source": 'list', "options": {}},
    104: {"name": 'Floor Curing Current Stage Set Temperature', "portal_label": 'Floor Curing Current Stage Set Temperature', "confidence": 'unverified', "min": 0, "max": 100, "range_source": 'list', "options": {}},
    105: {"name": 'Floor Curing Current Stage Valid Running Duration', "portal_label": 'Floor Curing Current Stage Valid Running Duration', "confidence": 'unverified', "min": 0, "max": 100, "range_source": 'list', "options": {}},
    106: {"name": 'Floor Curing Total Running Duration', "portal_label": 'Floor Curing Total Running Duration', "confidence": 'unverified', "min": 0, "max": 100, "range_source": 'list', "options": {}},
    107: {"name": 'Highest Water Temp. in Floor Curing Operation', "portal_label": 'Highest Water Temp. in Floor Curing Operation', "confidence": 'unverified', "min": 0, "max": 100, "range_source": 'list', "options": {}},
    108: {"name": 'Ambient Temp. to Activate First Class Anti-freezing', "portal_label": 'Ambient Temp. to Activate First Class Anti-freezing', "confidence": 'unverified', "min": 5, "max": 10, "range_source": 'list', "options": {}},
    109: {"name": 'Ambient Temp. to Activate Second Class Anti-freezing', "portal_label": 'Ambient Temp. to Activate Second Class Anti-freezing', "confidence": 'unverified', "min": 0, "max": 4, "range_source": 'list', "options": {}},
    110: {"name": 'Ambient Temp. to Stop Second Class Anti-freezing', "portal_label": 'Ambient Temp. to Stop Second Class Anti-freezing', "confidence": 'unverified', "min": 0, "max": 10, "range_source": 'list', "options": {}},
    111: {"name": 'Water Temp. to Activate Second Class Anti-freezing', "portal_label": 'Water Temp. to Activate Second Class Anti-freezing', "confidence": 'unverified', "min": 5, "max": 30, "range_source": 'list', "options": {}},
    112: {"name": 'Water Temp. to Stop Second Class Anti-freezing', "portal_label": 'Water Temp. to Stop Second Class Anti-freezing', "confidence": 'unverified', "min": 5, "max": 30, "range_source": 'list', "options": {}},
    114: {"name": 'Mode Switch during Defrosting', "portal_label": 'Mode Switch during Defrosting', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    116: {"name": 'Motorized Diverting Valve switching time', "portal_label": 'Motorized Diverting Valve switching time', "confidence": 'unverified', "min": 0, "max": 16, "range_source": 'list', "options": {}},
    117: {"name": 'Power On Time for Motorized Diverting Valve', "portal_label": 'Power On Time for Motorized Diverting Valve', "confidence": 'unverified', "min": 0, "max": 16, "range_source": 'list', "options": {}},
    118: {"name": 'Fan Speed Limit', "portal_label": 'Fan Speed Limit', "confidence": 'unverified', "min": 90, "max": 100, "range_source": 'list', "options": {}},
    119: {"name": 'Mode Signal Output', "portal_label": 'Mode Signal Output', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'No Output', 1: 'Heating', 2: 'Cooling'}},
    120: {"name": 'Mode Signal Type', "portal_label": 'Mode Signal Type', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'Normally Close', 1: 'Normally Open'}},
    121: {"name": 'Curve 1 parallel offset', "portal_label": 'Curve 1 Parallel Move', "confidence": 'verified', "min": -3, "max": 3, "range_source": 'form', "options": {}},
    122: {"name": 'Curve 2 parallel offset', "portal_label": 'Curve 2 Parallel Move', "confidence": 'verified', "min": -3, "max": 3, "range_source": 'form', "options": {}},
    124: {"name": 'DHW ECO Function', "portal_label": 'DHW ECO Function', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    125: {"name": 'DHW ECO Starting Ambient Temp.', "portal_label": 'DHW ECO Starting Ambient Temp.', "confidence": 'unverified', "min": -20, "max": 43, "range_source": 'list', "options": {}},
    126: {"name": 'Heating ECO Operation', "portal_label": 'Heating ECO Operation', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    127: {"name": 'Ambient Temp. to Start\xa0Heating ECO Operation', "portal_label": 'Ambient Temp. to Start\xa0Heating ECO Operation', "confidence": 'unverified', "min": -20, "max": 433, "range_source": 'list', "options": {}},
    128: {"name": 'Tw Sensor Dropped From its Position', "portal_label": 'Tw Sensor Dropped From its Position', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    129: {"name": 'Signal for Cutting Outdoor Unit Power Supply', "portal_label": 'Signal for Cutting Outdoor Unit Power Supply', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    130: {"name": 'Ambient Temp. to Stop Cutting Outdoor Unit Power Supply', "portal_label": 'Ambient Temp. to Stop Cutting Outdoor Unit Power Supply', "confidence": 'unverified', "min": -5, "max": 25, "range_source": 'list', "options": {}},
    131: {"name": 'Speed setting of Circulation Pump in Heating Operation', "portal_label": 'Speed setting of Circulation Pump in Heating Operation', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'High Speed', 1: 'Medium Speed', 2: 'Low Speed'}},
    132: {"name": 'Speed setting of Circulation Pump in Cooling Operation', "portal_label": 'Speed setting of Circulation Pump in Cooling Operation', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'High Speed', 1: 'Medium Speed', 2: 'Low Speed'}},
    133: {"name": 'Speed setting of Circulation Pump in DHW Operation', "portal_label": 'Speed setting of Circulation Pump in DHW Operation', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'High Speed', 1: 'Medium Speed', 2: 'Low Speed'}},
    134: {"name": 'Block the Working of Auxiliary Heater (AH)', "portal_label": 'Block the Working of Auxiliary Heater (AH)', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    135: {"name": 'Block the Working of Auxiliary Heater (AH) According to Ambient Temp.', "portal_label": 'Block the Working of Auxiliary Heater (AH) According to Ambient Temp.', "confidence": 'unverified', "min": None, "max": None, "range_source": None, "options": {0: 'OFF', 1: 'ON'}},
    136: {"name": 'Set Ambient Temp. to Block the Working of Auxiliary Heater', "portal_label": 'Set Ambient Temp. to Block the Working of Auxiliary Heater', "confidence": 'unverified', "min": -20, "max": 30, "range_source": 'list', "options": {}},
}

UNLABELLED_SETTINGS = (14, 15, 16, 17, 18, 113, 115, 123)


def option_label(options: dict[int, str] | None, value: Any) -> str | None:
    """Return the option text only for a finite whole-number value listed in options."""
    if not options or value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or not number.is_integer():
        return None
    return options.get(int(number))


def live_portal_attributes(index: int) -> dict[str, Any]:
    """Portal realdata address for a live-frame index (mapping only, not label verification)."""
    if index < 3:
        return {}
    return {"portal_realdata_parameter": f"par{index - LIVE_PORTAL_OFFSET}"}


def setting_attributes(index: int, value: Any) -> dict[str, Any]:
    """Attributes for a settings-frame value; the raw state itself is never rounded or mapped."""
    attrs: dict[str, Any] = {"portal_setdata_parameter": f"par{index}"}
    field = SETTINGS_FIELDS.get(index)
    if field is None:
        attrs["label_confidence"] = "unknown"
        return attrs
    attrs["label_confidence"] = field["confidence"]
    if field["portal_label"]:
        attrs["portal_label"] = field["portal_label"]
    if field["options"]:
        attrs["options"] = {str(key): text for key, text in field["options"].items()}
        attrs["options_source"] = OPTIONS_SOURCE
        label = option_label(field["options"], value)
        if label is not None:
            attrs["value_label"] = label
    if field["range_source"]:
        attrs["portal_range"] = [field["min"], field["max"]]
        attrs["portal_range_source"] = RANGE_SOURCES[field["range_source"]]
    return attrs


def setting_name(index: int) -> str:
    """Entity name for a settings-frame value: portal label plus the setdata parameter."""
    field = SETTINGS_FIELDS.get(index)
    return f"{field['name']} (par{index})" if field else f"Setting {index:03d}"
