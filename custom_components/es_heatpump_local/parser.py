"""Pure-Python frame parser for the ES heat pump local TCP protocol."""

from __future__ import annotations

from dataclasses import dataclass
import struct

from .const import (
    FRAME_END,
    FRAME_MAGIC,
    FRAME_TYPE_LONG,
    FRAME_TYPE_SHORT,
    LONG_SENSOR_COUNT,
    SHORT_SENSOR_COUNT,
)


# The length field counts the type byte, two more bytes and the values. The longest frame seen
# (170 values, panel program V2.38) declares 683; anything far beyond is not a frame.
MAX_DECLARED_LENGTH = 2048


@dataclass(slots=True, frozen=True)
class ParsedFrame:
    """A decoded protocol frame."""

    frame_type: int
    values: dict[str, float]
    checksum: int
    raw: bytes


def extract_frames(buffer: bytearray) -> list[bytes]:
    """Extract all complete frames from a TCP stream buffer."""
    frames: list[bytes] = []

    while True:
        start = buffer.find(FRAME_MAGIC)
        if start == -1:
            if len(buffer) > len(FRAME_MAGIC) - 1:
                del buffer[: -(len(FRAME_MAGIC) - 1)]
            break

        if start > 0:
            del buffer[:start]

        if len(buffer) < 15:
            break

        declared = int.from_bytes(buffer[10:12], "little")
        if not 3 <= declared <= MAX_DECLARED_LENGTH:
            # Not a frame start (or a damaged length field). Waiting for that many bytes
            # would swallow the real frames that follow: move on by one byte instead.
            del buffer[:1]
            continue
        total_length = declared + 15

        if len(buffer) < total_length:
            break

        if buffer[total_length - 1] != FRAME_END:
            # Resync: the stream looked frame-like but the terminator is wrong.
            del buffer[:1]
            continue

        frames.append(bytes(buffer[:total_length]))
        del buffer[:total_length]

    return frames


def parse_frame(frame: bytes) -> ParsedFrame:
    """Decode a single complete frame into float sensors.

    The panel program sends more values in newer versions: V2.05 sends 45 live and 136
    settings values, V2.38 sends 45 or 67 live and 138 or 170 settings values. The known
    values keep their positions, so a longer frame is accepted and its extra values get
    the next numbers. A frame with fewer values than the known set is rejected.
    """
    frame_type = frame[12]
    payload = frame[15:-3]
    checksum = int.from_bytes(frame[-3:-1], "little")

    if len(payload) % 4 != 0:
        raise ValueError(f"Frame payload size is not a multiple of 4: {len(payload)}")

    values = struct.unpack("<" + "f" * (len(payload) // 4), payload)

    if frame_type == FRAME_TYPE_SHORT:
        minimum_count = SHORT_SENSOR_COUNT
        keys = [f"short_{idx:02d}" for idx in range(1, len(values) + 1)]
    elif frame_type == FRAME_TYPE_LONG:
        minimum_count = LONG_SENSOR_COUNT
        keys = [f"long_{idx:03d}" for idx in range(1, len(values) + 1)]
    else:
        minimum_count = 0
        keys = [f"type_{frame_type:02d}_{idx:03d}" for idx in range(1, len(values) + 1)]

    if len(values) < minimum_count:
        raise ValueError(
            f"Too few values for frame type {frame_type}: {len(values)} < {minimum_count}"
        )

    parsed_values = {key: round(value, 4) for key, value in zip(keys, values, strict=True)}
    return ParsedFrame(
        frame_type=frame_type,
        values=parsed_values,
        checksum=checksum,
        raw=frame,
    )
