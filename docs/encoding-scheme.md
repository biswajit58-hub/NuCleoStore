# Encoding scheme

## Bit-to-nucleotide mapping

NucleoStore uses a fixed 2-bit to 1-nucleotide mapping:

| binary | DNA |
|--------|-----|
| 00     | A   |
| 01     | T   |
| 10     | G   |
| 11     | C   |

This is deliberately simple: it is a bijection (every byte maps to exactly one DNA string, every DNA string maps back to exactly one byte sequence), it does not lose leading zeros, and it has no ambiguity.

## Container header

Before encoding, payload bytes are wrapped:

The header makes the .dna file self-describing: it carries the original filename and a cryptographic checksum of the payload. Decoding is a two-step verification:

1. Structural: MAGIC matches, version supported, lengths consistent
2. Cryptographic: sha256 of the extracted payload matches the one in the header

Only if both pass is the payload written back to disk.

## Why a header at all

Without it, a .dna file is just A/T/G/C, and the decoder cannot tell you what the original file was called, whether the bytes are complete, or whether this is a NucleoStore file at all. The header solves all three, and makes the file portable across machines without any server-side manifest.

## Format evolution

- v1 (current): MAGIC + version + filename + size + sha256 + payload
- Future v2: add per-block Reed-Solomon parity and a compression flag

## What a real DNA storage system would add

| Layer | Purpose |
|---|---|
| Compression (zstd) | DNA is ~1000x more expensive per byte than disk; compress first |
| Constrained coding | Avoid homopolymers (AAAA) and GC extremes - synthesis error sources |
| Forward error correction | Reed-Solomon or fountain codes per block |
| Indexing | Multiple strands per file, addressable retrieval |
| Physical layer | Actual synthesis and sequencing (NGS) |
| Error model | Substitution, insertion, deletion, dropout - all occur |

NucleoStore implements the encoding/decoding core only. The above are the domain of a production system.