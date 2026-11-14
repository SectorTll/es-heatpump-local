"""Synthetic protocol and localhost checks; no vendor firmware or device captures."""
import asyncio
import importlib
import struct
import unittest
from unittest.mock import patch

from ha_stubs import load_coordinator_module

coordinator = load_coordinator_module("v238_under_test")
commands = importlib.import_module("v238_under_test.commands")
parser = importlib.import_module("v238_under_test.parser")
IDENTITY_A = bytes.fromhex("0102030405060708")
# The existing stream framing supports unit prefix 01; vary the module address.
IDENTITY_B = bytes.fromhex("0122334455667788")


def frame(kind=1, count=45, identity=IDENTITY_A, value=42.0):
    payload = b"\x00\x00" + struct.pack(f"<{count}f", *([value] * count))
    body = identity + struct.pack("<H", len(payload) + 1) + bytes([kind]) + payload
    return b"\xaa\x55" + body + struct.pack("<H", commands.crc16(body)) + b":"


class Writer:
    def __init__(self, blocked=False):
        self.writes = []
        self.closed = False
        self.aborted = False
        self.blocked = blocked
        self.transport = self

    def get_extra_info(self, name):
        return ("192.0.2.1", 40000) if name == "peername" else None

    def write(self, data):
        self.writes.append(data)

    def is_closing(self):
        return self.closed

    def get_write_buffer_size(self):
        return sum(map(len, self.writes)) if self.blocked else 0

    def close(self):
        self.closed = True

    def abort(self):
        self.aborted = self.closed = True

    async def wait_closed(self):
        pass

    async def drain(self):
        pass


class FrameTests(unittest.TestCase):
    def test_legacy_and_extended_payloads_keep_known_positions(self):
        for kind, count in ((1, 45), (1, 67), (2, 136), (2, 138), (2, 170)):
            with self.subTest(kind=kind, count=count):
                raw = frame(kind, count)
                self.assertTrue(commands.well_formed(raw))
                decoded = parser.parse_frame(raw).values
                self.assertEqual(len(decoded), count)
                self.assertEqual(decoded["short_09" if kind == 1 else "long_055"], 42.0)
                last = f"short_{count:02d}" if kind == 1 else f"long_{count:03d}"
                self.assertEqual(decoded[last], 42.0)

    def test_control_frames_only_allow_acknowledgements_and_read_requests(self):
        for kind in (3, 4, 6, 7):
            raw = commands.build_control(kind, IDENTITY_B)
            self.assertEqual(raw[:13], b"\x55\xaa" + IDENTITY_B + b"\x01\x00" + bytes([kind]))
            self.assertEqual(len(raw), 16)
            self.assertEqual(raw[-1], 0x3A)
            self.assertEqual(int.from_bytes(raw[-3:-1], "little"), commands.crc16(raw[2:-3]))
        for kind in (0, 1, 2, 5, 8):
            with self.assertRaises(ValueError):
                commands.build_control(kind, IDENTITY_A)
        for identity in (None, "0102030405060708", b"", b"1234567", b"123456789"):
            with self.assertRaises(ValueError):
                commands.build_control(3, identity)

    def test_ack_requires_matching_identity_and_intact_frame(self):
        for kind, count in ((1, 67), (2, 170)):
            raw = frame(kind, count)
            self.assertEqual(commands.acknowledgement(raw, IDENTITY_A),
                             commands.build_control(kind + 2, IDENTITY_A))
            self.assertIsNone(commands.acknowledgement(raw, IDENTITY_B))
            for offset in (0, 2, 10, 18, -3, -1):
                damaged = bytearray(raw)
                damaged[offset] ^= 1
                self.assertIsNone(commands.acknowledgement(damaged, IDENTITY_A))
        self.assertIsNone(commands.acknowledgement(frame(9, 1), IDENTITY_A))

    def test_length_and_terminator_damage_resynchronizes(self):
        good = frame(2, 170)
        for length in (0, 2, 65535):
            damaged = bytearray(frame())
            damaged[10:12] = struct.pack("<H", length)
            buffer = bytearray(damaged + good)
            self.assertEqual(parser.extract_frames(buffer), [good])
            self.assertEqual(buffer, b"")
        damaged = bytearray(frame())
        damaged[-1] = 0
        self.assertEqual(parser.extract_frames(bytearray(damaged + good)), [good])

    def test_too_short_or_unaligned_values_rejected(self):
        for kind, count in ((1, 44), (2, 135)):
            with self.assertRaises(ValueError):
                parser.parse_frame(frame(kind, count))
        raw = frame()
        with self.assertRaises(ValueError):
            parser.parse_frame(raw[:20] + raw[21:])


class ListenerTests(unittest.IsolatedAsyncioTestCase):
    def make(self):
        return coordinator.ESHeatpumpLocalCoordinator(None, "127.0.0.1", 0)

    async def consume(self, instance, data, writer=None):
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()
        writer = writer or Writer()
        await asyncio.wait_for(instance._handle_client(reader, writer), 1)
        self.assertEqual(instance._data["connected_clients"], 0)
        self.assertEqual(instance._channels, {})
        return writer

    async def test_ack_each_legacy_and_extended_frame_in_order(self):
        instance = self.make()
        packets = [frame(kind, count) for kind, count in ((1, 45), (2, 136), (1, 67), (2, 138), (2, 170))]
        writer = await self.consume(instance, b"".join(packets))
        self.assertEqual([raw[12] for raw in writer.writes], [3, 4, 3, 4, 4])
        self.assertEqual(instance._data["short_frames_received"], 2)
        self.assertEqual(instance._data["long_frames_received"], 3)
        self.assertEqual(instance._data["long_170"], 42)

    async def test_ack_precedes_entity_updates(self):
        instance, writer = self.make(), Writer()
        apply = instance._apply_frame

        def assert_ack_then_apply(parsed):
            self.assertEqual(writer.writes[-1][12], parsed.frame_type + 2)
            apply(parsed)

        instance._apply_frame = assert_ack_then_apply
        await self.consume(instance, frame() + frame(2, 170), writer)
        self.assertEqual(instance._data["frames_received"], 2)

    async def test_damaged_or_unusable_frames_do_not_select_identity(self):
        bad = bytearray(frame(identity=IDENTITY_A))
        bad[-3] ^= 1
        instance = self.make()
        # Unknown type, too few values and CRC damage must not pin discovery to A.
        data = bytes(bad) + frame(9, 1) + frame(1, 3) + frame(2, 170, IDENTITY_B)
        writer = await self.consume(instance, data)
        self.assertEqual(writer.writes, [commands.build_control(4, IDENTITY_B)])
        self.assertEqual(instance._data["short_frames_received"], 0)
        self.assertEqual(instance._data["long_frames_received"], 1)

    async def test_identity_change_ignored_then_relearned_on_reconnect(self):
        instance = self.make()
        writer = await self.consume(instance, frame() + frame(identity=IDENTITY_B, value=99))
        self.assertEqual(len(writer.writes), 1)
        self.assertEqual(instance._data["short_09"], 42)
        writer = await self.consume(instance, frame(identity=IDENTITY_B, value=43))
        self.assertEqual(writer.writes, [commands.build_control(3, IDENTITY_B)])
        self.assertEqual(instance._data["short_09"], 43)

    async def test_discovery_never_enables_settings_writes(self):
        instance, reader, writer = self.make(), asyncio.StreamReader(), Writer()
        task = asyncio.create_task(instance._handle_client(reader, writer))
        reader.feed_data(frame(2, 170))
        try:
            for _ in range(100):
                if writer.writes:
                    break
                await asyncio.sleep(0.001)
            self.assertEqual(len(writer.writes), 1)
            self.assertIsNone(commands.IDENTITY)
            self.assertIsNone(coordinator.IDENTITY)
            with self.assertRaisesRegex(ValueError, "disabled"):
                await instance.async_test_dhw_target(49, 42)
            channel = instance._channels[writer]
            self.assertIsNone(channel.latest)
            with self.assertRaisesRegex(ValueError, "disabled"):
                await channel.send(49, 42)
            self.assertEqual([raw[12] for raw in writer.writes], [4])
        finally:
            reader.feed_eof()
            await asyncio.wait_for(task, 1)

    async def test_requests_wait_for_identity_and_are_rate_limited(self):
        instance, reader, writer = self.make(), asyncio.StreamReader(), Writer()
        with (patch.object(coordinator, "CHECK_INTERVAL", 0.005),
              patch.object(coordinator, "FIRST_REQUEST_AGE", 0),
              patch.object(coordinator, "REQUEST_REPEAT", 10),
              patch.object(coordinator, "REQUESTS", ((1, 6, 0.01), (2, 7, 0.01)))):
            task = asyncio.create_task(instance._handle_client(reader, writer))
            try:
                await asyncio.sleep(0.03)
                self.assertEqual(writer.writes, [])
                reader.feed_data(frame(identity=IDENTITY_B))
                for _ in range(200):
                    if len(writer.writes) >= 3:
                        break
                    await asyncio.sleep(0.005)
                await asyncio.sleep(0.03)
                self.assertEqual(sorted(raw[12] for raw in writer.writes), [3, 6, 7])
                self.assertTrue(all(raw[2:10] == IDENTITY_B for raw in writer.writes))
            finally:
                reader.feed_eof()
                await asyncio.wait_for(task, 1)

    async def test_silent_peer_is_closed_without_sending_anything(self):
        instance, reader, writer = self.make(), asyncio.StreamReader(), Writer()
        with (patch.object(coordinator, "CHECK_INTERVAL", 0.005),
              patch.object(coordinator, "SILENCE_BEFORE_CLOSE", 0.01)):
            await asyncio.wait_for(instance._handle_client(reader, writer), 1)
        self.assertTrue(writer.closed)
        self.assertEqual(writer.writes, [])
        self.assertEqual(instance._channels, {})

    async def test_os_timeout_does_not_spin(self):
        instance, reader, writer = self.make(), asyncio.StreamReader(), Writer()
        reader.set_exception(TimeoutError("socket timeout"))
        await asyncio.wait_for(instance._handle_client(reader, writer), 1)
        self.assertTrue(writer.closed)
        self.assertEqual(instance._channels, {})

    async def test_backpressure_aborts_connection(self):
        instance, writer = self.make(), Writer(blocked=True)
        with patch.object(coordinator, "UNSENT_LIMIT", 10):
            await self.consume(instance, frame(), writer)
        self.assertTrue(writer.aborted)

    async def test_localhost_fragmentation_ack_and_clean_stop(self):
        instance = self.make()
        await instance.async_start()
        port = instance._server.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        try:
            data = frame(1, 67, IDENTITY_B) + frame(2, 170, IDENTITY_B)
            for i in range(0, len(data), 7):
                writer.write(data[i:i + 7])
                await writer.drain()
                await asyncio.sleep(0)
            response = await asyncio.wait_for(reader.readexactly(32), 2)
            self.assertEqual(response, commands.build_control(3, IDENTITY_B) + commands.build_control(4, IDENTITY_B))
            self.assertEqual(instance._data["frames_received"], 2)
            self.assertIsNone(commands.IDENTITY)
            await asyncio.wait_for(instance.async_stop(), 2)
            self.assertEqual(await asyncio.wait_for(reader.read(), 2), b"")
        finally:
            writer.close()
            await writer.wait_closed()
            await instance.async_stop()


if __name__ == "__main__":
    unittest.main()
