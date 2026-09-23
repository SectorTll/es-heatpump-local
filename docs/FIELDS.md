# Field dictionary

Generated from `custom_components/es_heatpump_local/fields.py` (settings) and `sensor.py` (live values).

Two portal namespaces reuse the same `parN` names: live value `NN` = realdata `par(NN-2)`; setting `long_NNN` = setdata `parNNN`.

## Live values changed in 0.2.0

| Live | Realdata | Name | Label confidence | Note |
|---|---|---|---|---|
| 17 | par15 | P0-Correlated Signal (unidentified) | inferred | follows circulation pump P0 (live 35) within ~10 s on the reference unit; meaning unknown |
| 24/25 | par22/par23 | High/Low Pressure (Pd/Ps) | portal diagram | attribute `pressure_reference: gauge (inferred)` |
| 28 | par26 | Suction Temp (Ts) | portal diagram | was unnamed; unit °C added |
| 29 | par27 | Outdoor Coil Temp (Tp) | portal diagram | was mislabelled Suction Temp (Ts) |
| 31 | par29 | Fan Speed 2 | portal diagram | unit rpm added; 0 on single-fan units, not physically verified |
| 40 | par38 | Compressor Control Level (inferred) | inferred | dimensionless 0-10 step (portal: Calculated Comp. Speed), not Hz |
| 41 | par39 | Suction Superheat (inferred) | inferred | controller-reported, K; ≈ Ts − Tsat(Ps + 1 bar) on the reference R410A unit |
| 42 | par40 | Discharge Superheat (inferred) | inferred | controller-reported, K; ≈ Td − Tsat(Pd + 1 bar) on the reference R410A unit |

## Settings (`long_NNN` = setdata `parNNN`)

72 verified, 56 unverified, unknown: long_014, long_015, long_016, long_017, long_018, long_113, long_115, long_123.
Ranges and options are portal reference data, not safe write limits.

| long | Name | Label confidence | Range (source) | Options |
|---|---|---|---|---|
| 001 | Unit ON/OFF (par1) | verified |  | 0=OFF; 1=ON |
| 002 | Software version (par2) | verified | 0…1000 (form) |  |
| 003 | Database version (par3) | verified | 0…100 (form) |  |
| 004 | Configured working mode (par4) | verified |  | 0=Standby; 1=Heating; 2=Cooling; 3=Sanitary Hot Water; 4=Auto |
| 005 | Language (par5) | verified |  | 0=English; 1=Slovenščina; 2=Deutsch; 3=Polski; 4=Italiano; 5=Русский; 6=Українська; 7=Polski; 8=English; 9=English; 10=English; 11=English; 12=English; 13=English; 14=English; 15=中文 |
| 006 | Sanitary Hot Water (par6) | unverified |  | 0=OFF; 1=ON |
| 007 | Heating (par7) | unverified |  | 0=OFF; 1=ON |
| 008 | Cooling (par8) | unverified |  | 0=OFF; 1=ON |
| 009 | Heating/cooling switch source (par9) | verified |  | 0=Invalid; 1=Ambient Temp.; 2=External Signal Control; 3=External Signal Control+Ambient Temp. |
| 010 | Basic Operation Modes (par10) | unverified |  | 0=OFF; 1=ON |
| 011 | Ambient temperature to start heating (par11) | verified | -10…25 (form) |  |
| 012 | Ambient temperature to start cooling (par12) | verified | 8…53 (form) |  |
| 013 | Max Allowed Duration For Min Compressor Speed (par13) | unverified | 5…60 (list) |  |
| 019 | Heating/cooling timer enabled (par19) | verified |  | 0=OFF; 1=ON |
| 020 | Heating/cooling stop delta T (par20) | verified | 1…3 (form) |  |
| 021 | Heating/cooling restart delta T (par21) | verified | 1…10 (form) |  |
| 022 | Compressor speed reduction delta T (par22) | verified | 1…10 (form) |  |
| 023 | Cooling setpoint circuit 1 (par23) | verified | 0…100 (form) |  |
| 024 | Heating curve circuit 1 enabled (par24) | verified |  | 0=OFF; 1=ON |
| 025 | Curve 1 ambient point A (par25) | verified | -25…35 (form) |  |
| 026 | Curve 1 ambient point B (par26) | verified | -25…35 (form) |  |
| 027 | Curve 1 ambient point C (par27) | verified | -25…35 (form) |  |
| 028 | Curve 1 ambient point D (par28) | verified | -25…35 (form) |  |
| 029 | Curve 1 ambient point E (par29) | verified | -25…35 (form) |  |
| 030 | Curve 1 water point A (par30) | verified | 20…60 (form) |  |
| 031 | Curve 1 water point B (par31) | verified | 20…60 (form) |  |
| 032 | Curve 1 water point C (par32) | verified | 20…60 (form) |  |
| 033 | Curve 1 water point D (par33) | verified | 20…60 (form) |  |
| 034 | Curve 1 water point E (par34) | verified | 20…60 (form) |  |
| 035 | Room temperature effect on heating curve (par35) | verified |  | 0=OFF; 1=ON |
| 036 | Ideal room temperature heating (par36) | verified | 15…35 (form) |  |
| 037 | Ideal room temperature cooling (par37) | verified | 15…35 (form) |  |
| 038 | Fixed heating setpoint circuit 1 (par38) | verified | 20…60 (form) |  |
| 039 | Low Temperature Limit (par39) | unverified | 7…60 (list) |  |
| 040 | High Temperature Limit (par40) | unverified | 7…75 (list) |  |
| 041 | Anti-legionella program enabled (par41) | verified |  | 0=OFF; 1=ON |
| 042 | Anti-legionella setpoint (par42) | verified | 60…80 (form) |  |
| 043 | Anti-legionella duration (par43) | verified | 5…60 (form) |  |
| 044 | Anti-legionella finish time (par44) | verified | 10…180 (form) |  |
| 045 | Vacation mode enabled (par45) | verified |  | 0=OFF; 1=ON |
| 046 | Vacation DHW temperature drop (par46) | verified | 10…50 (form) |  |
| 047 | Vacation heating water temperature drop (par47) | verified | 10…50 (form) |  |
| 048 | Heating backup source enabled (par48) | verified |  | 0=OFF; 1=ON |
| 049 | HBH priority relative to AH (par49) | verified |  | 0=Lower than AH; 1=Higher than AH |
| 050 | DHW backup source enabled (par50) | verified |  | 0=OFF; 1=ON |
| 051 | HWTBH priority relative to AH (par51) | verified |  | 0=Lower than AH; 1=Higher than AH |
| 052 | HBH accumulating threshold (par52) | verified | 5…600 (form) |  |
| 053 | HWTBH water temperature reading interval (par53) | verified | 5…180 (form) |  |
| 054 | Emergency Operation (par54) | unverified |  | 0=OFF; 1=ON |
| 055 | DHW main setpoint (par55) | verified | 25…75 (form) |  |
| 056 | DHW main restart delta T (par56) | verified | 2…15 (form) |  |
| 057 | Priority shifting enabled (par57) | verified |  | 0=OFF; 1=ON |
| 058 | Priority shifting starting temperature (par58) | verified | -15…20 (form) |  |
| 059 | Minimum DHW working time (par59) | verified | 10…60 (form) |  |
| 060 | Maximum heating working time (par60) | verified | 30…180 (form) |  |
| 061 | Allowable heating temperature drift (par61) | verified | 3…10 (form) |  |
| 062 | DHW backup heater for priority shifting (par62) | verified |  | 0=OFF; 1=ON |
| 063 | DHW storage function enabled (par63) | verified |  | 0=OFF; 1=ON |
| 064 | DHW reheating enabled (par64) | verified |  | 0=OFF; 1=ON |
| 065 | DHW reheating setpoint (par65) | verified | 25…55 (form) |  |
| 066 | DHW reheating restart delta T (par66) | verified | 2…20 (form) |  |
| 067 | Circuit 2 enabled (par67) | verified |  | 0=OFF; 1=ON |
| 068 | Cooling setpoint circuit 2 (par68) | verified | 0…100 (form) |  |
| 069 | Heating curve circuit 2 enabled (par69) | verified |  | 0=OFF; 1=ON |
| 070 | Curve 2 water point A (par70) | verified | -666…666 (form) |  |
| 071 | Curve 2 water point B (par71) | verified | -666…666 (form) |  |
| 072 | Curve 2 water point C (par72) | verified | -666…666 (form) |  |
| 073 | Curve 2 water point D (par73) | verified | -666…666 (form) |  |
| 074 | Curve 2 water point E (par74) | verified | -666…666 (form) |  |
| 075 | Fixed heating setpoint circuit 2 (par75) | verified | 0…100 (form) |  |
| 076 | High Temperature Limit (par76) | unverified | 7…75 (list) |  |
| 077 | Low Temperature Limit (par77) | unverified | 7…60 (list) |  |
| 078 | Reduced setpoint enabled (par78) | verified |  | 0=OFF; 1=ON |
| 079 | Reduced setpoint temperature offset (par79) | verified | 2…10 (form) |  |
| 080 | Quiet operation enabled (par80) | verified |  | 0=OFF; 1=ON |
| 081 | Quiet operation allowable temperature drift (par81) | verified | 2…10 (form) |  |
| 082 | Operation Signal for Electrical Utility Lock (par82) | unverified |  | 0=Normally Close; 1=Normally Open |
| 083 | Utility lock enabled (par83) | verified |  | 0=OFF; 1=ON |
| 084 | HBH during utility lock (par84) | verified |  | 0=OFF; 1=ON |
| 085 | P0 during utility lock (par85) | verified |  | 0=OFF; 1=ON |
| 086 | Panel backlight timeout (par86) | verified |  | 0=Allways ON; 1=3 min.; 2=5 min.; 3=10 min. |
| 087 | Circulation Pump P0 Type (par87) | unverified |  | 0=DC Variable Speed Pump (PWM control); 1=AC Pump |
| 088 | Speed Setting of Circulation Pump P0 (par88) | unverified |  | 0=High Speed; 1=Medium Speed; 2=Low Speed |
| 089 | Working Mode of Circulation Pump P0 (par89) | unverified |  | 0=Interval working mode; 1=ON Constantly; 2=OFF with Compressor |
| 090 | Pump Off Interval for P0 (par90) | unverified | 5…60 (list) |  |
| 091 | Pump On Time for P0 (par91) | unverified | 1…10 (list) |  |
| 092 | Buffer Tank (par92) | unverified |  | 0=OFF; 1=ON |
| 093 | Mixing Valve (par93) | unverified |  | 0=OFF; 1=ON |
| 094 | Mixing Valve (par94) | unverified |  | 0=OFF; 1=ON |
| 095 | P1 for Heating Operation (par95) | unverified |  | 0=OFF; 1=ON |
| 096 | P1 for Cooling Operation (par96) | unverified |  | 0=OFF; 1=ON |
| 097 | P1 with High Temp. Demand (par97) | unverified |  | 0=OFF; 1=ON |
| 098 | P2 for Heating Operation (par98) | unverified |  | 0=OFF; 1=ON |
| 099 | P2 for Cooling Operation (par99) | unverified |  | 0=OFF; 1=ON |
| 100 | P2 with High Temp. Demand (par100) | unverified |  | 0=OFF; 1=ON |
| 101 | Floor Curing (par101) | unverified |  | 0=OFF; 1=ON |
| 102 | Floor Curing Current Stage (par102) | unverified | 0…16 (list) |  |
| 103 | Floor Curing Current Stage Running Duration (par103) | unverified | -50…500 (list) |  |
| 104 | Floor Curing Current Stage Set Temperature (par104) | unverified | 0…100 (list) |  |
| 105 | Floor Curing Current Stage Valid Running Duration (par105) | unverified | 0…100 (list) |  |
| 106 | Floor Curing Total Running Duration (par106) | unverified | 0…100 (list) |  |
| 107 | Highest Water Temp. in Floor Curing Operation (par107) | unverified | 0…100 (list) |  |
| 108 | Ambient Temp. to Activate First Class Anti-freezing (par108) | unverified | 5…10 (list) |  |
| 109 | Ambient Temp. to Activate Second Class Anti-freezing (par109) | unverified | 0…4 (list) |  |
| 110 | Ambient Temp. to Stop Second Class Anti-freezing (par110) | unverified | 0…10 (list) |  |
| 111 | Water Temp. to Activate Second Class Anti-freezing (par111) | unverified | 5…30 (list) |  |
| 112 | Water Temp. to Stop Second Class Anti-freezing (par112) | unverified | 5…30 (list) |  |
| 114 | Mode Switch during Defrosting (par114) | unverified |  | 0=OFF; 1=ON |
| 116 | Motorized Diverting Valve switching time (par116) | unverified | 0…16 (list) |  |
| 117 | Power On Time for Motorized Diverting Valve (par117) | unverified | 0…16 (list) |  |
| 118 | Fan Speed Limit (par118) | unverified | 90…100 (list) |  |
| 119 | Mode Signal Output (par119) | unverified |  | 0=No Output; 1=Heating; 2=Cooling |
| 120 | Mode Signal Type (par120) | unverified |  | 0=Normally Close; 1=Normally Open |
| 121 | Curve 1 parallel offset (par121) | verified | -3…3 (form) |  |
| 122 | Curve 2 parallel offset (par122) | verified | -3…3 (form) |  |
| 124 | DHW ECO Function (par124) | unverified |  | 0=OFF; 1=ON |
| 125 | DHW ECO Starting Ambient Temp. (par125) | unverified | -20…43 (list) |  |
| 126 | Heating ECO Operation (par126) | unverified |  | 0=OFF; 1=ON |
| 127 | Ambient Temp. to Start Heating ECO Operation (par127) | unverified | -20…433 (list) |  |
| 128 | Tw Sensor Dropped From its Position (par128) | unverified |  | 0=OFF; 1=ON |
| 129 | Signal for Cutting Outdoor Unit Power Supply (par129) | unverified |  | 0=OFF; 1=ON |
| 130 | Ambient Temp. to Stop Cutting Outdoor Unit Power Supply (par130) | unverified | -5…25 (list) |  |
| 131 | Speed setting of Circulation Pump in Heating Operation (par131) | unverified |  | 0=High Speed; 1=Medium Speed; 2=Low Speed |
| 132 | Speed setting of Circulation Pump in Cooling Operation (par132) | unverified |  | 0=High Speed; 1=Medium Speed; 2=Low Speed |
| 133 | Speed setting of Circulation Pump in DHW Operation (par133) | unverified |  | 0=High Speed; 1=Medium Speed; 2=Low Speed |
| 134 | Block the Working of Auxiliary Heater (AH) (par134) | unverified |  | 0=OFF; 1=ON |
| 135 | Block the Working of Auxiliary Heater (AH) According to Ambient Temp. (par135) | unverified |  | 0=OFF; 1=ON |
| 136 | Set Ambient Temp. to Block the Working of Auxiliary Heater (par136) | unverified | -20…30 (list) |  |
| 014 | Setting 014 | unknown | | |
| 015 | Setting 015 | unknown | | |
| 016 | Setting 016 | unknown | | |
| 017 | Setting 017 | unknown | | |
| 018 | Setting 018 | unknown | | |
| 113 | Setting 113 | unknown | | |
| 115 | Setting 115 | unknown | | |
| 123 | Setting 123 | unknown | | |
