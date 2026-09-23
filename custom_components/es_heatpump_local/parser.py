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
        total_length = declared + 15

        if len(buffer) < total_length:
            break

        frame = bytes(buffer[:total_length])
        del buffer[:total_length]

        if frame[-1] != FRAME_END:
            # Resync: the stream looked frame-like but the terminator is wrong.
            continue

        frames.append(frame)

    return frames


def parse_frame(frame: bytes) -> ParsedFrame:
    """Decode a single complete frame into float sensors."""
    frame_type = frame[12]
    payload = frame[15:-3]
    checksum = int.from_bytes(frame[-3:-1], "little")

    if len(payload) % 4 != 0:
        raise ValueError(f"Frame payload size is not a multiple of 4: {len(payload)}")

    values = struct.unpack("<" + "f" * (len(payload) // 4), payload)

    if frame_type == FRAME_TYPE_SHORT:
        expected_count = SHORT_SENSOR_COUNT
        keys = [f"short_{idx:02d}" for idx in range(1, expected_count + 1)]
    elif frame_type == FRAME_TYPE_LONG:
        expected_count = LONG_SENSOR_COUNT
        keys = [f"long_{idx:03d}" for idx in range(1, expected_count + 1)]
    else:
        keys = [f"type_{frame_type:02d}_{idx:03d}" for idx in range(1, len(values) + 1)]
        expected_count = len(values)

    if len(values) != expected_count:
        raise ValueError(
            f"Unexpected float count for frame type {frame_type}: {len(values)} != {expected_count}"
        )

    parsed_values = {key: round(value, 4) for key, value in zip(keys, values, strict=True)}
    return ParsedFrame(
        frame_type=frame_type,
        values=parsed_values,
        checksum=checksum,
        raw=frame,
    )
