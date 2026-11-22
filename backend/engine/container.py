"""Self-describing DNA container format for NucleoStore.

Version 1: MAGIC | version(1) | filename_len(4) | filename | size(8) | sha256(32) | payload
Version 2: MAGIC | version(1) | coding(1) | filename_len(4) | filename | size(8) | sha256(32) | payload

coding byte: 0 = no error correction, 1 = 3x repetition.
"""

import hashlib
import struct

MAGIC = b"NUCLEO1"
VERSION_LEGACY = 1
VERSION_CURRENT = 2
_HEADER_FIXED_V1 = len(MAGIC) + 1 + 4
_HEADER_FIXED_V2 = len(MAGIC) + 1 + 1 + 4
_TRAILER_FIXED = 8 + 32

CODING_NONE = 0
CODING_REP3 = 1


class ContainerError(Exception):
    pass


def pack(payload: bytes, filename: str, coding: int = CODING_NONE) -> bytes:
    """Wrap payload bytes in a v2 container header."""
    name_bytes = filename.encode("utf-8")
    if len(name_bytes) > 0xFFFFFFFF:
        raise ContainerError("Filename too long")
    if coding not in (CODING_NONE, CODING_REP3):
        raise ContainerError(f"Unknown coding value {coding}")
    sha = hashlib.sha256(payload).digest()
    header = (
        MAGIC
        + bytes([VERSION_CURRENT])
        + bytes([coding])
        + struct.pack(">I", len(name_bytes))
        + name_bytes
        + struct.pack(">Q", len(payload))
        + sha
    )
    return header + payload


def is_container(data: bytes) -> bool:
    return len(data) >= len(MAGIC) and data[:len(MAGIC)] == MAGIC


def unpack(data: bytes) -> dict:
    if not is_container(data):
        raise ContainerError("Not a NucleoStore .dna file (bad magic)")
    if len(data) < len(MAGIC) + 1:
        raise ContainerError("Container truncated")
    version = data[len(MAGIC)]
    if version == VERSION_LEGACY:
        return _unpack_v1(data)
    if version == VERSION_CURRENT:
        return _unpack_v2(data)
    raise ContainerError(f"Unsupported container version {version}")


def _unpack_v1(data: bytes) -> dict:
    if len(data) < _HEADER_FIXED_V1:
        raise ContainerError("v1 container truncated")
    (name_len,) = struct.unpack(">I", data[len(MAGIC) + 1 : len(MAGIC) + 5])
    name_start = _HEADER_FIXED_V1
    name_end = name_start + name_len
    if len(data) < name_end + _TRAILER_FIXED:
        raise ContainerError("v1 container truncated inside filename/trailer")
    filename = data[name_start:name_end].decode("utf-8", errors="strict")
    (payload_size,) = struct.unpack(">Q", data[name_end : name_end + 8])
    sha = data[name_end + 8 : name_end + 40]
    payload = data[name_end + 40 :]
    if len(payload) != payload_size:
        raise ContainerError(f"Payload size mismatch: header={payload_size} actual={len(payload)}")
    actual = hashlib.sha256(payload).digest()
    if actual != sha:
        raise ContainerError("SHA-256 mismatch in container header")
    return {
        "filename": filename,
        "payload": payload,
        "sha256": sha.hex(),
        "coding": CODING_NONE,
        "version": VERSION_LEGACY,
    }


def _unpack_v2(data: bytes) -> dict:
    if len(data) < _HEADER_FIXED_V2:
        raise ContainerError("v2 container truncated")
    coding = data[len(MAGIC) + 1]
    (name_len,) = struct.unpack(">I", data[len(MAGIC) + 2 : len(MAGIC) + 6])
    name_start = _HEADER_FIXED_V2
    name_end = name_start + name_len
    if len(data) < name_end + _TRAILER_FIXED:
        raise ContainerError("v2 container truncated inside filename/trailer")
    filename = data[name_start:name_end].decode("utf-8", errors="strict")
    (payload_size,) = struct.unpack(">Q", data[name_end : name_end + 8])
    sha = data[name_end + 8 : name_end + 40]
    payload = data[name_end + 40 :]
    if len(payload) != payload_size:
        raise ContainerError(f"Payload size mismatch: header={payload_size} actual={len(payload)}")
    actual = hashlib.sha256(payload).digest()
    if actual != sha:
        raise ContainerError("SHA-256 mismatch in container header")
    return {
        "filename": filename,
        "payload": payload,
        "sha256": sha.hex(),
        "coding": coding,
        "version": VERSION_CURRENT,
    }