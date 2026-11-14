# Telemetry transport in 0.3.0-alpha.1

This documents the observed protocol and the scope of validation. It is not a complete vendor specification or a guide to changing heat-pump settings.

## Frames and replies

The pump pushes binary frames through its serial-to-TCP bridge. A received frame has an `AA 55` prefix, an eight-byte protocol identity, a little-endian length, a type, payload, CRC16/Modbus and a `3A` terminator. The existing stream matcher supports an identity starting with unit prefix `01`. Other unit prefixes have not been validated.

| Direction | Type | Meaning |
| --- | --- | --- |
| Pump → HA | 1 | Current readings |
| Pump → HA | 2 | Settings snapshot |
| HA → pump | 3 | Acknowledge current readings |
| HA → pump | 4 | Acknowledge settings snapshot |
| HA → pump | 6 | Request current readings |
| HA → pump | 7 | Request settings snapshot |

Replies start with `55 AA`. ACK and read-request packets contain no settings payload. The experimental type-5 setting command remains disabled in the public package.

| Panel software | Live field counts | Settings field counts |
| --- | --- | --- |
| V2.05 | 45 | 136 |
| V2.38 | 45 or 67 | 138 or 170 |

The parser accepts complete float payloads containing at least the known 45/136 fields, within a 2048-byte declared-length limit. Known field positions are preserved. Only the existing 45 live and 136 settings sensors are created; additional values remain internal until their mapping and entity behavior are defined.

Frame counters count received messages, including repeated snapshots with unchanged values. They do not count parameters changed on the pump.

## Connection identity and timing

The public listener learns the telemetry address from its first usable live/settings frame after checking CRC, framing and payload size. Unknown frame types, corrupt frames and short payloads do not choose the address. A different address on that same connection is ignored; reconnecting starts discovery again. This keeps replies scoped to the connection and never assigns the separate `IDENTITY` write pin.

This is routing, not authentication. Use one pump per listener on a trusted LAN. No write support is granted by connecting or supplying a valid frame.

An ACK is queued before an accepted live/settings frame updates entities. Missing live data is requested after 30 seconds and settings after 45 seconds, checked every 5 seconds. Each request type is limited to once per 15 seconds. On a fresh connection a missing frame type becomes eligible after 10 seconds, but no requests are sent until valid telemetry has supplied the address. A completely silent connection closes after 120 seconds. Queued output over 16 KiB closes a peer that is not reading.

Invalid CRC frames are neither acknowledged nor published. Implausible length fields and bad terminators trigger resynchronization. Payloads too short for the known layout are skipped. Received values remain available after disconnection; inspect the last-frame timestamp and connection diagnostics for freshness.

## What was tested

- The shared ACK/request transport was deployed on the reference V2.05 installation under Home Assistant 2026.11.1. Both live and settings frames continued arriving after restart. That private installation uses a fixed, verified device identity.
- V2.38's extended frames and ACK behavior were checked in a local panel-code emulator with a serial-bridge stand-in. This is not a physical-panel test or a guarantee for other firmware builds.
- This public variant discovers a telemetry identity per connection. Its 36 offline tests cover synthetic identities, old and extended frame sizes, CRC damage, stream resynchronization, ACK ordering, refusal of setting writes after discovery, missing-update requests, timeout handling, backpressure and fragmented messages over a real localhost TCP connection. Home Assistant classes are stubbed.
- The public discovery variant has not yet been deployed on a second installation. No vendor executable, database, private identifier, device capture or emulator image is included in the repository or required by its tests.

Smart Grid, additional sensor mapping and generalized setting writes remain separate research topics.
