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
from .commands import (
    IDENTITY,
    REQUEST_LIVE,
    REQUEST_SETTINGS,
    CommandChannel,
    acknowledgement,
    build_control,
    well_formed,
)

_LOGGER = logging.getLogger(__name__)

# Seconds. A pump whose frames are acknowledged sends live values every 10 s while they change
# and at least once a minute, and its settings once a minute. Request missing updates to
# maintain fresh monitoring. Requests start only after valid telemetry supplies an identity;
# there is no device-specific identity or command authorization in the public build.
CHECK_INTERVAL = 5
LIVE_REQUEST_AGE = 30
SETTINGS_REQUEST_AGE = 45
FIRST_REQUEST_AGE = 10
REQUEST_REPEAT = 15
SILENCE_BEFORE_CLOSE = 120
# Bytes written to a peer that does not read them pile up in memory. The pump's bridge reads at
# once; a connection that lets this much pile up is not the bridge and is closed.
UNSENT_LIMIT = 16384
REQUESTS = (
    (FRAME_TYPE_SHORT, REQUEST_LIVE, LIVE_REQUEST_AGE),
    (FRAME_TYPE_LONG, REQUEST_SETTINGS, SETTINGS_REQUEST_AGE),
)


def _close(writer) -> None:
    """Close a connection without waiting for bytes the peer has not taken.

    An ordinary close first delivers everything that was written. A peer that has stopped
    reading would keep the connection, and with it the stop of the integration, waiting for ever.
    """
    if writer.transport.get_write_buffer_size():
        writer.transport.abort()
    else:
        writer.close()


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
            _close(writer)
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

        connected = time.monotonic()
        last_data = connected
        # As if the last frame of each kind had come so long ago that the first request is due
        # FIRST_REQUEST_AGE seconds from now, unless the pump sends that kind by itself before.
        last_frame = {frame_type: connected + FIRST_REQUEST_AGE - age for frame_type, _, age in REQUESTS}
        last_request = {frame_type: float("-inf") for frame_type, _, _ in REQUESTS}
        # Learn only from a usable, CRC-checked telemetry frame. Never use this value
        # as the experimental write pin. A new connection starts discovery afresh.
        telemetry_identity = None
        foreign_reported = unusable_reported = False
        try:
            # Inside the try: whatever an entity raises here, the finally below still takes the
            # connection out of the table and closes it.
            self.async_set_updated_data(dict(self._data))
            _LOGGER.info("ES Heatpump Local: client connected from %s", peer_text)
            while True:
                try:
                    async with asyncio.timeout(CHECK_INTERVAL) as waiting:
                        chunk = await reader.read(4096)
                except TimeoutError:
                    # The operating system's "connection timed out" is the same exception class.
                    # It stays on the reader, every further read would fail at once, and treating
                    # it as "nothing arrived yet" would spin here without ever yielding.
                    if not waiting.expired() or reader.exception() is not None:
                        raise
                    chunk = None
                now = time.monotonic()

                if chunk is not None:
                    if not chunk:
                        break
                    last_data = now
                    buffer.extend(chunk)
                    for frame in extract_frames(buffer):
                        if not well_formed(frame):
                            # The checksum does not match: bytes were damaged on the way. Such a
                            # frame is neither answered nor shown; the pump sends the next one.
                            _LOGGER.debug("ES Heatpump Local: damaged frame from %s ignored", peer_text)
                            continue
                        try:
                            parsed = parse_frame(frame)
                        except ValueError as err:
                            if not unusable_reported:
                                unusable_reported = True
                                _LOGGER.warning(
                                    "ES Heatpump Local: a frame from %s cannot be used: %s. "
                                    "Further such frames on this connection are not reported",
                                    peer_text, err,
                                )
                            continue
                        if telemetry_identity is None and frame[12] in (FRAME_TYPE_SHORT, FRAME_TYPE_LONG):
                            telemetry_identity = frame[2:10]
                        if telemetry_identity is not None and frame[2:10] != telemetry_identity:
                            if not foreign_reported:
                                foreign_reported = True
                                _LOGGER.warning(
                                    "ES Heatpump Local: %s changed protocol identity on an established "
                                    "connection; frames from the other identity are ignored until reconnect",
                                    peer_text,
                                )
                            continue
                        # The vendor server acknowledges every live and settings frame. Panel
                        # program V2.38 needs that to accept a setting; V2.05 does not mind.
                        # The acknowledgement goes out before the frame is used, so a command
                        # triggered by this frame can never overtake it.
                        answer = acknowledgement(frame, telemetry_identity)
                        if answer:
                            if not writer.is_closing():     # the peer may be gone while its last frames are worked through
                                writer.write(answer)
                            last_frame[frame[12]] = now
                        channel.observe(frame)
                        self._apply_frame(parsed)
                elif now - last_data >= SILENCE_BEFORE_CLOSE:
                    _LOGGER.info(
                        "ES Heatpump Local: closing silent connection from %s after %s s",
                        peer_text, SILENCE_BEFORE_CLOSE,
                    )
                    break

                for frame_type, request, age in REQUESTS:
                    if (telemetry_identity is not None and now - last_frame[frame_type] >= age
                            and now - last_request[frame_type] >= REQUEST_REPEAT):
                        if not writer.is_closing():
                            writer.write(build_control(request, telemetry_identity))
                        last_request[frame_type] = now

                if writer.transport.get_write_buffer_size() > UNSENT_LIMIT:
                    _LOGGER.info("ES Heatpump Local: closing %s, it does not read what is sent to it", peer_text)
                    break
        except OSError as err:
            # The bridge restarted or the network dropped: ordinary, the bridge connects again.
            _LOGGER.info("ES Heatpump Local: connection from %s lost: %r", peer_text, err)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("ES Heatpump Local: error on the connection from %s", peer_text)
        finally:
            channel.disconnected()
            self._channels.pop(writer, None)
            self._client_counter = max(0, self._client_counter - 1)
            self._data["connected_clients"] = self._client_counter
            try:
                self.async_set_updated_data(dict(self._data))
            except Exception:  # noqa: BLE001
                _LOGGER.exception("ES Heatpump Local: error while reporting the end of the connection from %s", peer_text)
            try:
                _close(writer)
                await writer.wait_closed()
            except OSError as err:  # e.g. ConnectionResetError when the bridge resets the socket
                _LOGGER.debug("ES Heatpump Local: %s closed with %r", peer_text, err)
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
