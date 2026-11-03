"""Minimal parser/builder for Miele DOP2 payloads (reverse-engineered from the Miele@mobile app)."""
from __future__ import annotations

import struct
from typing import Any

# value size in bytes per type byte; 0x10 is a nested struct
_SIZES = {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 2, 8: 4, 9: 4, 0x0B: 8}
HEADER = 10  # length, unit, attribute, idx1, idx2 (2 bytes each)


class _Unknown(Exception):
    """A field type we do not know; everything parsed before it is kept."""


def _parse(b: bytes, o: int, out: dict[int, Any]) -> int:
    (n,) = struct.unpack_from(">H", b, o)
    o += 2
    for _ in range(n):
        fid, t = struct.unpack_from(">HB", b, o)
        o += 3
        if t == 0x10:
            out[fid] = {}
            o = _parse(b, o, out[fid])
        elif t in _SIZES:
            out[fid] = int.from_bytes(b[o : o + _SIZES[t]], "big")
            o += _SIZES[t]
        else:
            raise _Unknown(t)
    return o


def parse(b: bytes) -> dict[int, Any]:
    """Parse a DOP2 leaf response into {field id: value or nested dict}."""
    out: dict[int, Any] = {}
    try:
        _parse(b, HEADER, out)
    except _Unknown:
        pass  # later parts of some leaves use types we do not decode; the earlier parts are kept
    return out


def build_oven_setpoint(program_id: int, centi_celsius: int) -> bytes:
    """Body for PUT DOP2/2/1577 that changes the temperature of the running oven program.

    Layout seen in the app: field 1 = program id, field 2 = 6 (parameter: temperature),
    field 3 = 2, field 7 = {6: temperature in 1/100 degC}.
    """
    pl = (
        struct.pack(">HHBH", 4, 1, 7, program_id)
        + struct.pack(">HBB", 3, 4, 2)
        + struct.pack(">HBH", 2, 5, 6)
        + struct.pack(">HBH", 7, 0x10, 1)
        + struct.pack(">HBH", 6, 5, centi_celsius)
    )
    return struct.pack(">HHHHH", len(pl) + 8, 2, 1577, 0, 0) + pl
