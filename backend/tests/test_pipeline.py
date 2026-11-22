import hashlib
import os

import pytest

from backend.engine.pipeline import (
    encode_file, decode_file, IntegrityError, DecodeError, sha256_file,
)
from backend.engine.container import ContainerError


def test_pipeline_text_roundtrip(tmp_path):
    src = tmp_path / "hello.txt"
    src.write_text("NucleoStore pipeline works.", encoding="ascii")
    dna = tmp_path / "hello.dna"
    out = tmp_path / "hello.out"
    e = encode_file(src, dna)
    d = decode_file(dna, out, expected_sha256=e["sha256"])
    assert src.read_bytes() == out.read_bytes()
    assert d["sha256"] == e["sha256"]


def test_pipeline_empty_file(tmp_path):
    src = tmp_path / "empty.bin"
    src.write_bytes(b"")
    dna = tmp_path / "empty.dna"
    out = tmp_path / "empty.out"
    e = encode_file(src, dna)
    decode_file(dna, out, expected_sha256=e["sha256"])
    assert out.read_bytes() == b""


def test_pipeline_random_binary(tmp_path):
    src = tmp_path / "rand.bin"
    src.write_bytes(os.urandom(2048))
    dna = tmp_path / "rand.dna"
    out = tmp_path / "rand.out"
    e = encode_file(src, dna)
    decode_file(dna, out, expected_sha256=e["sha256"])
    assert sha256_file(src) == sha256_file(out)


def test_pipeline_detects_corruption(tmp_path):
    src = tmp_path / "data.txt"
    src.write_text("one two three", encoding="ascii")
    dna = tmp_path / "data.dna"
    out = tmp_path / "data.out"
    e = encode_file(src, dna)
    original_dna = dna.read_text(encoding="ascii")
    corrupted = ("C" if original_dna[0] != "C" else "A") + original_dna[1:]
    dna.write_text(corrupted, encoding="ascii")
    with pytest.raises((IntegrityError, ContainerError, DecodeError)):
        decode_file(dna, out, expected_sha256=e["sha256"])


def test_storage_store_and_reconstruct(isolated_storage, tmp_path):
    storage = isolated_storage
    src = tmp_path / "upload.txt"
    src.write_bytes(b"Storage layer test payload.")

    record = storage.store_and_encode(src)
    assert record["job_id"]
    assert record["sha256"] == hashlib.sha256(b"Storage layer test payload.").hexdigest()

    result = storage.reconstruct(record["job_id"])
    reconstructed = tmp_path / "storage" / "reconstructed_files" / record["job_id"] / "upload.txt"
    assert reconstructed.read_bytes() == src.read_bytes()
    assert result["reconstructed_result"]["sha256"] == record["sha256"]


def test_storage_lists_jobs(isolated_storage, tmp_path):
    storage = isolated_storage
    for i in range(3):
        f = tmp_path / f"file{i}.txt"
        f.write_text(f"content {i}", encoding="ascii")
        storage.store_and_encode(f)
    jobs = storage.list_jobs()
    assert len(jobs) == 3


def test_storage_ecc_roundtrip(isolated_storage, tmp_path):
    storage = isolated_storage
    src = tmp_path / "ecc.txt"
    src.write_bytes(b"ecc test data")

    record = storage.store_and_encode(src, ecc=True)
    assert record["ecc"] == "rep3"
    assert record["coding"] == 1

    result = storage.reconstruct(record["job_id"])
    assert result["coding"] == 1
    reconstructed = tmp_path / "storage" / "reconstructed_files" / record["job_id"] / "ecc.txt"
    assert reconstructed.read_bytes() == b"ecc test data"