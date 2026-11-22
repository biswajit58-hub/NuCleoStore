BINARY_TO_DNA = {
    "00": "A",
    "01": "T",
    "10": "G",
    "11": "C",
}


def binary_to_dna(binary_str: str) -> str:
    if len(binary_str) % 2 != 0:
        raise ValueError(
            f"Binary string length must be even, got {len(binary_str)}"
        )
    if any(c not in "01" for c in binary_str):
        raise ValueError("Binary string may only contain '0' and '1'")
    return "".join(
        BINARY_TO_DNA[binary_str[i:i + 2]]
        for i in range(0, len(binary_str), 2)
    )