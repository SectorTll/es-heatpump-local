"""Bounded DHW setpoint control, based on verified local command encoding."""
import asyncio
import struct
import time

# The original installation's device identity is intentionally not distributed.
# Write support needs device-specific verification before it can be enabled.
IDENTITY: bytes | None = None


def crc16(data):
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def valid_frame(raw):
    return (len(raw) >= 18 and raw[:2] == b"\xaa\x55" and raw[2:10] == IDENTITY
            and len(raw) == int.from_bytes(raw[10:12], "little") + 15
            and raw[-1] == 0x3A and crc16(raw[2:-3]) == int.from_bytes(raw[-3:-1], "little"))


def build_dhw_command(value):
    if IDENTITY is None:
        raise ValueError("DHW writes are disabled in this public alpha; device-specific verification is required")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 45 <= value <= 55 or value != int(value):
        raise ValueError("DHW target must be a whole number from 45 to 55 C")
    body = IDENTITY + b"\x07\x00\x05" + struct.pack("<Hf", 54, value)
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
        if not valid_frame(raw) or raw[12] != 2 or len(raw) != 562:
            return
        self.latest = struct.unpack_from("<f", raw, 15 + 54 * 4)[0]
        self.updated = time.monotonic()
        if self.pending and not self.pending.done() and self.latest == self.target:
            self.pending.set_result(self.latest)

    def disconnected(self):
        if self.pending and not self.pending.done():
            self.pending.set_exception(ConnectionError("Disconnected; command outcome unknown. No automatic retry."))

    async def send(self, value, expected, timeout=90):
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
