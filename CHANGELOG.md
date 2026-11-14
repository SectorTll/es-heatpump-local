# Changelog

## 0.3.0-alpha.1

Feature release for the new telemetry transport. Supersedes the initial `0.2.2-alpha.1` publication with the same functionality.

- Accept extended HeatStar V2.38 telemetry: 45/67 live values and 138/170 settings, while retaining V2.05's 45/136 format. Existing entities keep their IDs; extra fields are parsed internally without creating new entities.
- Acknowledge valid live/settings frames (types 3/4) and request missing updates (types 6/7). Learn the telemetry identity from the first usable, CRC-checked frame on each connection. Ignore a different identity until reconnect; no original device identifiers are distributed. Settings writes remain disabled, including after telemetry discovery.
- Validate CRC before publishing telemetry, recover from implausible lengths and bad terminators, and skip unusable payloads. Close silent or backpressured connections and handle socket timeouts without a busy loop.
- Keep experimental DHW confirmation compatible with longer settings frames and a 150-second wait; it remains unavailable in the public build.
- Add synthetic frame, identity isolation, write-disable, request timing, backpressure and localhost TCP tests. All 36 offline tests pass locally.
- Validation limits: shared transport checked on the reference V2.05 installation; V2.38 checked in a local panel-code emulator, not on the physical panel. Public identity discovery checked offline and over localhost only. No firmware, databases or private captures are included.

## 0.2.2-alpha.1

- Initial publication of the transport changes described above. Superseded by `0.3.0-alpha.1` to identify this as a feature release; no functional changes between the two tags.

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
