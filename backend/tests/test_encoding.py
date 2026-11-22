import hashlib
import os

import pytest

from backend.engine.binary_converter import file_to_binary, binary_to_file, binary_to_bytes
from backend.engine.dna_encoder import binary_to_dna
from backend.engine.dna_decoder import dna_to_binary


def sha256_of(path) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def roundtrip(tmp_path, filename: str, payload: bytes) -> None:
    original = tmp_path / filename
    original.write_bytes(payload)
    dna = binary_to_dna(file_to_binary(str(original)))
    reconstructed = tmp_path / f"reconstructed_{filename}"
    binary_to_file(dna_to_binary(dna), str(reconstructed))
    assert sha256_of(original) == sha256_of(reconstructed)


def test_text_file_roundtrip(tmp_path):
    roundtrip(tmp_path, "sample.txt", b"Hello, NucleoStore! DNA storage works.\n")


def test_small_png_roundtrip(tmp_path):
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae"
        "426082"
    )
    roundtrip(tmp_path, "pixel.png", png)


def test_pdf_roundtrip(tmp_path):
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\n"
        b"xref\n0 3\n0000000000 65535 f \n"
        b"trailer<</Size 3/Root 1 0 R>>\n%%EOF\n"
    )
    roundtrip(tmp_path, "minimal.pdf", pdf)


def test_random_binary_roundtrip(tmp_path):
    roundtrip(tmp_path, "random.bin", os.urandom(4096))


def test_empty_file_roundtrip(tmp_path):
    roundtrip(tmp_path, "empty.bin", b"")


def test_leading_zeros_preserved(tmp_path):
    payload = bytes([0x00, 0x01, 0x02, 0x03, 0x00, 0x00, 0xFF])
    roundtrip(tmp_path, "zeros.bin", payload)
    original = tmp_path / "zeros2.bin"
    original.write_bytes(payload)
    bs = file_to_binary(str(original))
    assert bs[:8] == "00000000" and bs[8:16] == "00000001"


def test_decoder_rejects_invalid_nucleotide():
    with pytest.raises(ValueError):
        dna_to_binary("ATGCX")


def test_encoder_rejects_odd_length_binary():
    with pytest.raises(ValueError):
        binary_to_dna("000")


def test_encoder_rejects_non_binary_characters():
    with pytest.raises(ValueError):
        binary_to_dna("00x1")


def test_converter_rejects_incomplete_byte():
    with pytest.raises(ValueError):
        binary_to_bytes("0000")


def test_known_dna_mapping():
    assert binary_to_dna("00011011") == "ATGC"
    assert dna_to_binary("ATGC") == "00011011"