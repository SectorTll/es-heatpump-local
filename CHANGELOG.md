# Changelog

## 0.2.1-alpha.1

- A bridge that resets the TCP connection while it is being closed no longer logs a `ConnectionResetError` traceback; the channel, pending command and client counter are cleaned up as before, and reconnection works. Task cancellation is still propagated.
- Offline test for connection teardown (reset while closing, reconnect, cancellation).

## 0.2.0-alpha.1

- Settings: all 136 settings sensors are named from the myheatpump.com portal setdata labels (`<label> (parN)`): 72 `verified` against the reference installation, 56 `unverified`, 8 `unknown` (`Setting NNN`). Attributes: `portal_setdata_parameter`, `label_confidence`, `portal_label`, `options`, `value_label` (only for an exact listed whole number), `portal_range` with its source. Raw states are unchanged.
- Live values: `portal_realdata_parameter` (address `par(NN-2)`) and `label_confidence` for live 3-45; notes for inferred fields.
- Live 29 renamed to Outdoor Coil Temp (Tp) (was Suction Temp (Ts)); live 28 is Suction Temp (Ts), °C.
- Live 31 Fan Speed 2 (rpm); live 40 Compressor Control Level (inferred), dimensionless; live 41/42 Suction/Discharge Superheat (inferred), K with the temperature-difference device class where Home Assistant provides it; live 17 P0-Correlated Signal (unidentified).
- Live 24/25: attribute `pressure_reference: gauge (inferred)`.
- Reheating DHW target renamed (entity ID unchanged).
- Integer decoding for working mode, pump status and software version no longer fails on non-finite values.
- New offline tests for the field dictionary and sensor metadata; `docs/FIELDS.md`.

## 0.1.0-alpha.1

- Initial public monitoring alpha.
