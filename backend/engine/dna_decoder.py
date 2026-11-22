from backend.engine.dna_encoder import BINARY_TO_DNA

DNA_TO_BINARY = {v: k for k, v in BINARY_TO_DNA.items()}


def dna_to_binary(dna_str: str) -> str:
    parts = []
    for i, char in enumerate(dna_str):
        if char not in DNA_TO_BINARY:
            raise ValueError(
                f"Invalid DNA character at position {i}: {char!r}"
            )
        parts.append(DNA_TO_BINARY[char])
    return "".join(parts)