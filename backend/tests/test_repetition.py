import pytest
from backend.engine import repetition


def test_rep3_roundtrip():
    dna = "ATGCATGC"
    coded = repetition.encode_rep3(dna)
    assert coded == dna * 3
    assert repetition.decode_rep3(coded) == dna


def test_rep3_empty():
    assert repetition.encode_rep3("") == ""
    assert repetition.decode_rep3("") == ""


def test_rep3_corrects_single_substitution():
    dna = "ATGCATGC"
    coded = repetition.encode_rep3(dna)
    mutated = ("G" if coded[0] != "G" else "A") + coded[1:]
    assert repetition.decode_rep3(mutated) == dna


def test_rep3_corrects_multiple_positions_one_each():
    dna = "ATGCATGC"
    coded = list(repetition.encode_rep3(dna))
    coded[0] = "G" if coded[0] != "G" else "A"
    coded[len(dna) + 1] = "G" if coded[len(dna) + 1] != "G" else "A"
    coded[2 * len(dna) + 2] = "G" if coded[2 * len(dna) + 2] != "G" else "A"
    assert repetition.decode_rep3("".join(coded)) == dna

def test_rep3_rejects_non_multiple_of_3():
    with pytest.raises(ValueError):
        repetition.decode_rep3("ATGCATA")  # length 7, not divisible by 3


def test_rep3_rejects_no_majority():
    with pytest.raises(ValueError):
        repetition.decode_rep3("A" + "T" + "G")