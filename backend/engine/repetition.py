"""3x repetition error correction for DNA sequences.

Encodes a DNA string by repeating it 3 times in a row, allowing
1-nucleotide correction per position via majority vote on decode.

Note: repetition acts on the *whole* sequence, so any single
substitution anywhere is corrected. Insertions/deletions are not
handled (they shift the frame) - only substitutions.
"""


def encode_rep3(dna: str) -> str:
    """Repeat the DNA sequence 3 times."""
    if not dna:
        return ""
    return dna * 3


def decode_rep3(coded: str) -> str:
    """Recover the original by 3-way majority vote at each position."""
    if not coded:
        return ""
    if len(coded) % 3 != 0:
        raise ValueError(
            f"Rep3-coded DNA length must be multiple of 3, got {len(coded)}"
        )
    n = len(coded) // 3
    copy1 = coded[:n]
    copy2 = coded[n : 2 * n]
    copy3 = coded[2 * n :]

    out = []
    for a, b, c in zip(copy1, copy2, copy3):
        # Majority vote
        if a == b or a == c:
            out.append(a)
        elif b == c:
            out.append(b)
        else:
            raise ValueError(
                f"No majority at position: {a},{b},{c} - too many errors"
            )
    return "".join(out)