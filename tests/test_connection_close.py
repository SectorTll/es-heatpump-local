"""Offline checks of TCP connection teardown in the coordinator (no network, stubbed Home Assistant)."""
import asyncio
import importlib
import struct
import unittest

from ha_stubs import load_coordinator_module

coordinator_module = load_coordinator_module("coordinator_under_test")
commands = importlib.import_module("coordinator_under_test.commands")


def short_frame(tw=42.0):
    values = [0.0] * 45
    values[8] = tw
    payload = b"\x00\x00" + struct.pack("<45f", *values)
    body = bytes.fromhex("0102030405060708") + struct.pack("<H", len(payload) + 1) + bytes([1]) + payload
    return b"\xaa\x55" + body + struct.pack("<H", commands.crc16(body)) + b":"


class FakeReader:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def read(self, size):
        return await self.queue.get()


class FakeWriter:
    def __init__(self, close_error=None):
        self.close_error = close_error
        self.closed = False

    def get_extra_info(self, name):
        return ("192.0.2.10", 40000) if name == "peername" else None

    def is_closing(self):
        return self.closed

    def close(self):
        self.closed = True

    async def wait_closed(self):
        if self.close_error is not None:
            raise self.close_error

    def write(self, data):
        pass

    async def drain(self):
        pass


class ConnectionTeardownTests(unittest.IsolatedAsyncioTestCase):
    def make(self):
        return coordinator_module.ESHeatpumpLocalCoordinator(None, "0.0.0.0", 18899)

    async def test_reset_while_closing_is_contained_and_state_cleaned(self):
        coordinator = self.make()
        reader = FakeReader()
        writer = FakeWriter(ConnectionResetError(104, "Connection reset by peer"))
        task = asyncio.create_task(coordinator._handle_client(reader, writer))
        await asyncio.sleep(0)
        self.assertEqual(coordinator._data["connected_clients"], 1)
        channel = coordinator._channels[writer]
        channel.pending = asyncio.get_running_loop().create_future()
        await reader.queue.put(short_frame())
        await reader.queue.put(b"")
        await asyncio.wait_for(task, 1)
        self.assertEqual(coordinator._channels, {})
        self.assertEqual(coordinator._data["connected_clients"], 0)
        self.assertEqual(coordinator._data["frames_received"], 1)
        self.assertTrue(writer.closed)
        self.assertTrue(channel.pending.done())
        self.assertIsInstance(channel.pending.exception(), ConnectionError)

    async def test_reconnect_after_reset(self):
        coordinator = self.make()
        first_reader, first_writer = FakeReader(), FakeWriter(ConnectionResetError())
        await first_reader.queue.put(b"")
        await coordinator._handle_client(first_reader, first_writer)
        second_reader, second_writer = FakeReader(), FakeWriter()
        await second_reader.queue.put(short_frame(43.5))
        await second_reader.queue.put(b"")
        await coordinator._handle_client(second_reader, second_writer)
        self.assertEqual(coordinator._channels, {})
        self.assertEqual(coordinator._data["connected_clients"], 0)
        self.assertEqual(coordinator._data["frames_received"], 1)
        self.assertEqual(coordinator._data["short_09"], 43.5)
        self.assertEqual(max(update["connected_clients"] for update in coordinator.updates), 1)

    async def test_cancellation_is_not_swallowed(self):
        coordinator = self.make()
        reader, writer = FakeReader(), FakeWriter(asyncio.CancelledError())
        await reader.queue.put(b"")
        with self.assertRaises(asyncio.CancelledError):
            await coordinator._handle_client(reader, writer)
        self.assertEqual(coordinator._channels, {})
        self.assertEqual(coordinator._data["connected_clients"], 0)


if __name__ == "__main__":
    unittest.main()
