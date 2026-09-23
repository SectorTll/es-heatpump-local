"""Push coordinator for the ES heat pump local TCP listener."""

from __future__ import annotations

import asyncio
from datetime import datetime
import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN, FRAME_TYPE_LONG, FRAME_TYPE_SHORT
from .parser import extract_frames, parse_frame
from .commands import CommandChannel, IDENTITY

_LOGGER = logging.getLogger(__name__)


class ESHeatpumpLocalCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Receive pushed TCP frames and expose them as coordinator data."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self._host = host
        self._port = port
        self._server: asyncio.base_events.Server | None = None
        self._channels = {}
        self._frame_counter = 0
        self._short_frame_counter = 0
        self._long_frame_counter = 0
        self._client_counter = 0
        self._last_frame_at: datetime | None = None
        self._data: dict[str, Any] = {
            "connected_clients": 0,
            "frames_received": 0,
            "short_frames_received": 0,
            "long_frames_received": 0,
            "last_frame_type": "none",
            "last_frame_at": None,
            "last_checksum": None,
        }

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    async def async_start(self) -> None:
        """Start the TCP listener."""
        self.async_set_updated_data(dict(self._data))
        self._server = await asyncio.start_server(
            self._handle_client,
            host=self._host,
            port=self._port,
        )

    async def async_stop(self) -> None:
        """Stop the TCP listener."""
        if self._server is None:
            return

        self._server.close()
        for writer, channel in list(self._channels.items()):
            channel.disconnected()
            writer.close()
        await asyncio.gather(*(w.wait_closed() for w in list(self._channels)), return_exceptions=True)
        await self._server.wait_closed()
        self._server = None

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Read a full TCP stream and parse protocol frames out of it."""
        peer = writer.get_extra_info("peername")
        peer_text = f"{peer[0]}:{peer[1]}" if peer else "unknown"
        buffer = bytearray()
        channel = CommandChannel(writer)
        self._channels[writer] = channel

        self._client_counter += 1
        self._data["connected_clients"] = self._client_counter
        self.async_set_updated_data(dict(self._data))
        _LOGGER.info("ES Heatpump Local: client connected from %s", peer_text)

        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=120)
                if not chunk:
                    break

                buffer.extend(chunk)
                for frame in extract_frames(buffer):
                    parsed = parse_frame(frame)
                    channel.observe(frame)
                    self._apply_frame(parsed)
        except TimeoutError:
            _LOGGER.info("ES Heatpump Local: closing silent connection from %s after 120 s", peer_text)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("ES Heatpump Local: error while reading from %s", peer_text)
        finally:
            channel.disconnected()
            self._channels.pop(writer, None)
            self._client_counter = max(0, self._client_counter - 1)
            self._data["connected_clients"] = self._client_counter
            self.async_set_updated_data(dict(self._data))
            writer.close()
            await writer.wait_closed()
            _LOGGER.info("ES Heatpump Local: client disconnected from %s", peer_text)

    async def async_test_dhw_target(self, temperature, expected_temperature):
        if IDENTITY is None:
            raise ValueError("DHW writes are disabled in this public alpha; device-specific verification is required")
        channels = [c for c in self._channels.values()
                    if c.latest is not None and not c.writer.is_closing()
                    and time.monotonic() - c.updated <= 90]
        if len(channels) != 1:
            raise ValueError("Need exactly one fresh verified pump connection")
        return await channels[0].send(temperature, expected_temperature)

    def _apply_frame(self, parsed) -> None:
        """Merge a parsed frame into coordinator state and notify entities."""
        self._frame_counter += 1
        self._last_frame_at = dt_util.utcnow()

        if parsed.frame_type == FRAME_TYPE_SHORT:
            self._short_frame_counter += 1
            frame_name = "short"
        elif parsed.frame_type == FRAME_TYPE_LONG:
            self._long_frame_counter += 1
            frame_name = "long"
        else:
            frame_name = f"type_{parsed.frame_type}"

        self._data.update(parsed.values)
        self._data["frames_received"] = self._frame_counter
        self._data["short_frames_received"] = self._short_frame_counter
        self._data["long_frames_received"] = self._long_frame_counter
        self._data["last_frame_type"] = frame_name
        self._data["last_frame_at"] = self._last_frame_at
        self._data["last_checksum"] = parsed.checksum

        self.async_set_updated_data(dict(self._data))
