"""Bounded DHW setpoint control, based on verified local command encoding.

Frames to the pump: 55 AA, the eight identity bytes of the pump's Wi-Fi module, a length,
a type byte, an optional payload, a CRC and the terminator 3A. Types sent from here:
  3  acknowledgement of a live-values frame (type 1 from the pump)
  4  acknowledgement of a settings frame (type 2 from the pump)
  5  set one setting: index (uint16) and value (float32)
  6  request for a live-values frame
  7  request for a settings frame

The vendor server acknowledges every frame. Panel program V2.38 depends on that: it ignores
type 5 until it has received a type 4, and after some minutes without acknowledgements it
starts questioning its Wi-Fi module. V2.05 works with or without acknowledgements.
"""
import asyncio
import struct
import time

# The original installation's device identity is intentionally not distributed.
# This pin authorizes experimental writes; telemetry discovery must never set it.
IDENTITY: bytes | None = None

ACKNOWLEDGE_LIVE = 3
ACKNOWLEDGE_SETTINGS = 4
REQUEST_LIVE = 6
REQUEST_SETTINGS = 7

# A settings frame of V2.05: 15 header bytes, 136 values, CRC and terminator (562 bytes).
# Newer programs append values (138 or 170), the first 136 keep their meaning.
SETTINGS_FRAME_MINIMUM = 15 + 136 * 4 + 3
DHW_TARGET_INDEX = 54


def crc16(data):
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def well_formed(raw):
    """Start bytes, declared length, terminator and CRC are right. The sender is not checked."""
    return (len(raw) >= 18 and raw[:2] == b"\xaa\x55"
            and len(raw) == int.from_bytes(raw[10:12], "little") + 15
            and raw[-1] == 0x3A and crc16(raw[2:-3]) == int.from_bytes(raw[-3:-1], "little"))


def valid_frame(raw):
    """A well-formed frame from this pump's Wi-Fi module."""
    return well_formed(raw) and raw[2:10] == IDENTITY


def build_control(frame_type, identity):
    """A frame without payload: an acknowledgement (3, 4) or a request (6, 7)."""
    if frame_type not in (ACKNOWLEDGE_LIVE, ACKNOWLEDGE_SETTINGS, REQUEST_LIVE, REQUEST_SETTINGS):
        raise ValueError(f"Not a control frame type: {frame_type}")
    if not isinstance(identity, bytes) or len(identity) != 8:
        raise ValueError("A control frame requires an eight-byte protocol identity")
    body = identity + b"\x01\x00" + bytes([frame_type])
    return b"\x55\xaa" + body + struct.pack("<H", crc16(body)) + b":"


def acknowledgement(raw, identity):
    """The answer the pump expects for a frame it sent, or None for anything else.

    The listener learns an identity from valid telemetry for this connection only.
    This is a routing address, not authentication or permission to change settings.
    """
    if not well_formed(raw) or raw[2:10] != identity:
        return None
    if raw[12] == 1:
        return build_control(ACKNOWLEDGE_LIVE, identity)
    if raw[12] == 2:
        return build_control(ACKNOWLEDGE_SETTINGS, identity)
    return None


def build_dhw_command(value):
    if IDENTITY is None:
        raise ValueError("DHW writes are disabled in this public alpha; device-specific verification is required")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 45 <= value <= 55 or value != int(value):
        raise ValueError("DHW target must be a whole number from 45 to 55 C")
    body = IDENTITY + b"\x07\x00\x05" + struct.pack("<Hf", DHW_TARGET_INDEX, value)
    return b"\x55\xaa" + body + struct.pack("<H", crc16(body)) + b":"


class CommandChannel:
    def __init__(self, writer):
        self.writer = writer
        self.latest = None
        self.updated = 0
        self.pending = None
        self.target = None
        self.lock = asyncio.Lock()

    def observe(self, raw):
        if not valid_frame(raw) or raw[12] != 2 or len(raw) < SETTINGS_FRAME_MINIMUM:
            return
        self.latest = struct.unpack_from("<f", raw, 15 + DHW_TARGET_INDEX * 4)[0]
        self.updated = time.monotonic()
        if self.pending and not self.pending.done() and self.latest == self.target:
            self.pending.set_result(self.latest)

    def disconnected(self):
        if self.pending and not self.pending.done():
            self.pending.set_exception(ConnectionError("Disconnected; command outcome unknown. No automatic retry."))

    async def send(self, value, expected, timeout=150):
        command = build_dhw_command(value)
        async with self.lock:
            if self.writer.is_closing():
                raise ConnectionError("Pump connection is closing")
            if self.latest is None or time.monotonic() - self.updated > 90:
                raise ValueError("Need a fresh, CRC-verified long packet (at most 90 s old)")
            if self.latest != expected:
                raise ValueError(f"Expected {expected} C, received {self.latest} C; nothing sent")
            if value == expected:
                return {"previous": expected, "confirmed": value, "confirmation": "already_matches_fresh_long_packet", "sent": False}
            self.pending = asyncio.get_running_loop().create_future()
            self.target = value
            try:
                self.writer.write(command)
                await asyncio.wait_for(self.writer.drain(), 5)
                confirmed = await asyncio.wait_for(self.pending, timeout)
                return {"previous": expected, "confirmed": confirmed, "confirmation": "fresh_crc_valid_long_packet"}
            except asyncio.TimeoutError as err:
                raise TimeoutError("Command sent; confirmation timed out. Outcome unknown; do not retry blindly.") from err
            finally:
                self.pending = None
                self.target = None
