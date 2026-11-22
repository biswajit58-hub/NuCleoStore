\# NucleoStore



DNA-based digital data storage. Encode any file — image, PDF, video, arbitrary binary — into DNA nucleotide sequences (A, T, G, C), and decode the DNA back into the original file, byte-identical.



\## What it does



\- \*\*Encode:\*\* any file becomes a self-describing `.dna` text file containing only A/T/G/C characters

\- \*\*Decode:\*\* upload a `.dna` file anywhere, get the original file back — correct name, byte-identical, SHA-256 verified

\- \*\*Self-contained:\*\* the `.dna` file carries its own header (filename, size, checksum). No database, no manifest, no server lookup needed.

\- \*\*Verifiable:\*\* SHA-256 of the reconstructed file is checked against the hash embedded in the DNA.



\## Encoding scheme



Each 2 bits map to 1 nucleotide:



| bits | nucleotide |

|------|-----------|

| 00   | A         |

| 01   | T         |

| 10   | G         |

| 11   | C         |



So a 1 KB file becomes \~4 KB of DNA text (8 bits/byte → 4 nucleotides/byte).



Before encoding, the payload is wrapped in a container header:



The header makes the `.dna` file self-describing.



\## Stack



\- \*\*Backend:\*\* Python 3.13, FastAPI, Uvicorn

\- \*\*Frontend:\*\* Next.js 16, React, TypeScript

\- \*\*Tests:\*\* pytest, 34 tests across engine, container, pipeline, storage, and API



\## Quick start



\### Prerequisites



\- Python 3.10+

\- Node.js 18+



\### Setup (once)



```powershell

python -m venv .venv

.venv\\Scripts\\Activate.ps1

pip install -r requirements.txt

cd frontend

npm install

cd ..

Frontend (Next.js, :3000)

&#x20;       │  /api/\* rewrite

&#x20;       ▼

Backend (FastAPI, :8000)

&#x20;       │

&#x20;       ├── api/main.py          HTTP endpoints

&#x20;       ├── engine/

&#x20;       │   ├── container.py     header pack/unpack

&#x20;       │   ├── binary\_converter.py    file ↔ binary

&#x20;       │   ├── dna\_encoder.py   binary → ATGC

&#x20;       │   ├── dna\_decoder.py   ATGC → binary

&#x20;       │   ├── pipeline.py      high-level encode/decode

&#x20;       │   └── storage.py       UUID folders + manifest

&#x20;       ├── storage/

&#x20;       │   ├── original\_files/

&#x20;       │   ├── dna\_sequences/

&#x20;       │   └── reconstructed\_files/

&#x20;       └── tests/               34 pytest cases



Paste, save, close:



```markdown

\# Encoding scheme



\## Bit-to-nucleotide mapping



NucleoStore uses a fixed 2-bit → 1-nucleotide mapping:



| binary | DNA |

|--------|-----|

| 00     | A   |

| 01     | T   |

| 10     | G   |

| 11     | C   |



This is deliberately simple: it is a bijection (every byte → exactly one DNA string, every DNA string → exactly one byte sequence), it does not lose leading zeros, and it has no ambiguity.



More sophisticated encodings exist in the DNA storage literature (reverse-complement codes, GC-balanced codes, homopolymer-avoiding codes). They matter when the DNA is physically synthesized — synthesis errors correlate with certain patterns. For a software-only system, the simple 2-bit mapping is optimal.



\## Container header



Before encoding, payload bytes are wrapped:





