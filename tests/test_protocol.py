"""Offline protocol checks using synthetic frames, without Home Assistant."""
import asyncio
import importlib
from pathlib import Path
import struct
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
package = types.ModuleType("protocol_under_test")
package.__path__ = [str(ROOT / "custom_components/es_heatpump_local")]
sys.modules[package.__name__] = package
commands = importlib.import_module("protocol_under_test.commands")
parser = importlib.import_module("protocol_under_test.parser")
SYNTHETIC_ID = bytes.fromhex("0102030405060708")


def frame(kind=2, target=50):
    values = [0.0] * (136 if kind == 2 else 45)
    values[54 if kind == 2 else 8] = target
    payload = b"\x00\x00" + struct.pack("<" + "f" * len(values), *values)
    body = SYNTHETIC_ID + struct.pack("<H", len(payload) + 1) + bytes([kind]) + payload
    return b"\xaa\x55" + body + struct.pack("<H", commands.crc16(body)) + b":"


class Writer:
    def __init__(self):
        self.writes = []

    def is_closing(self):
        return False

    def write(self, data):
        self.writes.append(data)

    async def drain(self):
        pass


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    def test_crc_known_vector(self):
        self.assertEqual(commands.crc16(b"123456789"), 0x4B37)

    def test_fragmented_and_concatenated_stream(self):
        short, long = frame(1, 42), frame()
        buffer = bytearray(b"noise" + short[:20])
        self.assertEqual(parser.extract_frames(buffer), [])
        buffer.extend(short[20:] + long)
        self.assertEqual(parser.extract_frames(buffer), [short, long])
        self.assertEqual(buffer, b"")
        self.assertEqual(parser.parse_frame(short).values["short_09"], 42)
        self.assertEqual(parser.parse_frame(long).values["long_055"], 50)

    def test_rejects_wrong_field_count(self):
        raw = bytearray(frame(1))
        raw[12] = 2
        with self.assertRaises(ValueError):
            parser.parse_frame(raw)

    async def test_public_build_cannot_write(self):
        self.assertIsNone(commands.IDENTITY)
        writer = Writer()
        channel = commands.CommandChannel(writer)
        channel.observe(frame())
        self.assertIsNone(channel.latest)
        with self.assertRaisesRegex(ValueError, "disabled"):
            await channel.send(49, 50)
        self.assertEqual(writer.writes, [])

    def test_command_range_and_encoding(self):
        with patch.object(commands, "IDENTITY", SYNTHETIC_ID):
            for value in [True, 44, 56, 49.5, float("nan"), float("inf")]:
                with self.assertRaises(ValueError):
                    commands.build_dhw_command(value)
            raw = commands.build_dhw_command(49)
            self.assertEqual(raw[:2], b"\x55\xaa")
            self.assertEqual(struct.unpack_from("<Hf", raw, 13), (54, 49.0))
            self.assertEqual(int.from_bytes(raw[-3:-1], "little"), commands.crc16(raw[2:-3]))

    async def test_guards_and_confirmation(self):
        with patch.object(commands, "IDENTITY", SYNTHETIC_ID):
            writer = Writer()
            channel = commands.CommandChannel(writer)
            with self.assertRaises(ValueError):
                await channel.send(49, 50)
            channel.observe(frame())
            with self.assertRaises(ValueError):
                await channel.send(49, 48)
            channel.updated -= 91
            with self.assertRaises(ValueError):
                await channel.send(49, 50)
            self.assertEqual(writer.writes, [])
            channel.observe(frame())
            task = asyncio.create_task(channel.send(49, 50, timeout=1))
            await asyncio.sleep(0.01)
            bad = bytearray(frame(target=49))
            bad[-2] ^= 1
            channel.observe(bad)
            channel.observe(frame())
            self.assertFalse(task.done())
            channel.observe(frame(target=49))
            self.assertEqual((await task)["confirmed"], 49)
            self.assertEqual(len(writer.writes), 1)

    async def test_timeout_never_retries(self):
        with patch.object(commands, "IDENTITY", SYNTHETIC_ID):
            writer = Writer()
            channel = commands.CommandChannel(writer)
            channel.observe(frame())
            with self.assertRaises(TimeoutError):
                await channel.send(49, 50, timeout=0.01)
            self.assertEqual(len(writer.writes), 1)


if __name__ == "__main__":
    unittest.main()
