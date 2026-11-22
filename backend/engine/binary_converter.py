"""
binary_converter.py
-------------------
Converts between files on disk and their binary string representation.

A byte (0-255) is written as exactly 8 binary characters, e.g.:
    0x00 -> "00000000"
    0x01 -> "00000001"
    0xFF -> "11111111"

The fixed width of 8 is essential: it is what preserves leading zeros,
so that decoding produces byte-for-byte identical output.
"""


def file_to_binary(file_path: str) -> str:
    """Read a file in binary mode and return a binary string.

    Example: a file containing b'A' (0x41) becomes "01000001".
    """
    with open(file_path, "rb") as f:
        data = f.read()
    # format(byte, "08b") -> 8-bit zero-padded binary for each byte
    return "".join(format(byte, "08b") for byte in data)


def binary_to_bytes(binary_str: str) -> bytes:
    """Convert a binary string back into bytes.

    Raises ValueError if the length is not a multiple of 8, because
    a partial byte has no well-defined meaning.
    """
    if len(binary_str) % 8 != 0:
        raise ValueError(
            f"Binary string length must be a multiple of 8, got {len(binary_str)}"
        )

    out = bytearray()
    for i in range(0, len(binary_str), 8):
        chunk = binary_str[i:i + 8]
        # Guard against junk input like "0100000x"
        if any(c not in "01" for c in chunk):
            raise ValueError(f"Invalid binary chunk: {chunk!r}")
        out.append(int(chunk, 2))
    return bytes(out)


def binary_to_file(binary_str: str, output_path: str) -> None:
    """Write a binary string to a file as raw bytes."""
    data = binary_to_bytes(binary_str)
    with open(output_path, "wb") as f:
        f.write(data)