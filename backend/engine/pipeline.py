"""High-level file -> DNA -> file operations."""

import hashlib
from pathlib import Path

from backend.engine.binary_converter import binary_to_bytes
from backend.engine.dna_encoder import binary_to_dna
from backend.engine.dna_decoder import dna_to_binary
from backend.engine import container
from backend.engine import repetition


class IntegrityError(Exception):
    pass


class DecodeError(Exception):
    pass


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode_file(source: str | Path, dna_output: str | Path, ecc: bool = False) -> dict:
    source = Path(source)
    dna_output = Path(dna_output)
    payload = source.read_bytes()
    coding = container.CODING_REP3 if ecc else container.CODING_NONE
    wrapped = container.pack(payload, source.name, coding=coding)
    binary = "".join(format(b, "08b") for b in wrapped)
    dna = binary_to_dna(binary)
    if ecc:
        dna = repetition.encode_rep3(dna)
    dna_output.parent.mkdir(parents=True, exist_ok=True)
    dna_output.write_text(dna, encoding="ascii")
    return {
        "source": str(source),
        "dna_file": str(dna_output),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source_bytes": len(payload),
        "dna_length": len(dna),
        "ecc": ecc,
    }


def decode_file(dna_input: str | Path, reconstructed_output: str | Path,
                expected_sha256: str | None = None) -> dict:
    dna_input = Path(dna_input)
    reconstructed_output = Path(reconstructed_output)
    dna = dna_input.read_text(encoding="ascii").strip()

    parsed = _decode_any(dna)

    reconstructed_output.parent.mkdir(parents=True, exist_ok=True)
    reconstructed_output.write_bytes(parsed["payload"])

    actual = parsed["sha256"]
    if expected_sha256 is not None and actual != expected_sha256:
        raise IntegrityError(
            f"SHA-256 mismatch: expected {expected_sha256}, got {actual}"
        )

    return {
        "dna_file": str(dna_input),
        "reconstructed": str(reconstructed_output),
        "original_filename": parsed["filename"],
        "sha256": actual,
        "reconstructed_bytes": len(parsed["payload"]),
        "dna_length": len(dna),
        "coding": parsed["coding"],
        "version": parsed["version"],
    }


def _decode_any(dna: str):
    """Try plain decode, then rep3, returning the first that works."""
    errors = []

    # Attempt 1: plain (no repetition, or v1/v2 header with coding=0)
    try:
        binary = dna_to_binary(dna)
        wrapped = binary_to_bytes(binary)
        return container.unpack(wrapped)
    except Exception as e:
        errors.append(f"plain: {e}")

    # Attempt 2: as rep3 (3x repetition of the whole DNA string)
    if len(dna) % 3 == 0:
        try:
            plain = repetition.decode_rep3(dna)
            binary = dna_to_binary(plain)
            wrapped = binary_to_bytes(binary)
            return container.unpack(wrapped)
        except Exception as e:
            errors.append(f"rep3: {e}")

    raise DecodeError("Could not decode DNA. " + " | ".join(errors))


def decode_dna_bytes_to_file(dna_text: str, output_dir: str | Path) -> dict:
    parsed = _decode_any(dna_text.strip())
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / parsed["filename"]
    out_path.write_bytes(parsed["payload"])
    return {
        "reconstructed": str(out_path),
        "original_filename": parsed["filename"],
        "sha256": parsed["sha256"],
        "reconstructed_bytes": len(parsed["payload"]),
        "coding": parsed["coding"],
    }