import hashlib
import pytest
from backend.engine import container


def test_pack_unpack_roundtrip():
    payload = b"hello dna world"
    packed = container.pack(payload, "hello.txt")
    parsed = container.unpack(packed)
    assert parsed["payload"] == payload
    assert parsed["filename"] == "hello.txt"
    assert parsed["sha256"] == hashlib.sha256(payload).hexdigest()


def test_pack_empty_payload():
    packed = container.pack(b"", "empty.bin")
    parsed = container.unpack(packed)
    assert parsed["payload"] == b""
    assert parsed["filename"] == "empty.bin"


def test_unpack_rejects_bad_magic():
    with pytest.raises(container.ContainerError, match="magic"):
        container.unpack(b"NOTNUCLEO1....")


def test_unpack_rejects_truncation():
    packed = container.pack(b"data", "x.txt")
    with pytest.raises(container.ContainerError):
        container.unpack(packed[:-5])


def test_unpack_detects_payload_corruption():
    packed = bytearray(container.pack(b"original", "x.txt"))
    packed[-1] ^= 0xFF
    with pytest.raises(container.ContainerError, match="SHA-256"):
        container.unpack(bytes(packed))


def test_is_container():
    assert container.is_container(container.pack(b"", "a"))
    assert not container.is_container(b"ATGCATGC")
