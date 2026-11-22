content = '''"""FastAPI app for NucleoStore."""

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

import backend.engine.storage as storage
from backend.engine import container
from backend.engine.binary_converter import binary_to_bytes
from backend.engine.dna_decoder import dna_to_binary

app = FastAPI(title="NucleoStore", version="0.2.0")


def _record_or_404(job_id: str) -> dict:
    for job in storage.list_jobs():
        if job["job_id"] == job_id:
            return job
    raise HTTPException(status_code=404, detail=f"No job with id {job_id}")


def _absolute(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    if not p.is_absolute():
        p = storage.PROJECT_ROOT / p
    return p


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/encode")
async def encode(file: UploadFile = File(...), ecc: str = "none"):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)
    try:
        use_ecc = (ecc.lower() == "rep3")
        record = storage.store_and_encode(tmp_path, original_name=file.filename, ecc=use_ecc)
    finally:
        tmp_path.unlink(missing_ok=True)
    dna_path = _absolute(record["dna_file"])
    dna_preview = dna_path.read_text(encoding="ascii")[:80] if dna_path.exists() else ""
    return {
        "job_id": record["job_id"],
        "original_name": record["original_name"],
        "sha256": record["sha256"],
        "source_bytes": record["source_bytes"],
        "dna_length": record["dna_length"],
        "dna_preview": dna_preview,
        "ecc": record.get("ecc", "none"),
    }


@app.post("/decode/{job_id}")
def decode(job_id: str):
    try:
        record = storage.reconstruct(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"No job with id {job_id}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "job_id": record["job_id"],
        "original_name": record["original_name"],
        "reconstructed": record["reconstructed"],
        "sha256": record["sha256"],
        "verified": True,
    }


@app.post("/decode-file")
async def decode_file_endpoint(file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty upload")
    try:
        dna_text = raw.decode("ascii").strip()
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Uploaded file is not ASCII DNA")
    try:
        binary = dna_to_binary(dna_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid DNA: {e}")
    try:
        wrapped = binary_to_bytes(binary)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid binary payload: {e}")
    if not container.is_container(wrapped):
        raise HTTPException(status_code=400, detail="Missing NucleoStore header")
    try:
        parsed = container.unpack(wrapped)
    except container.ContainerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    tmpdir = Path(tempfile.mkdtemp())
    out_path = tmpdir / parsed["filename"]
    out_path.write_bytes(parsed["payload"])
    return FileResponse(path=str(out_path), media_type="application/octet-stream", filename=parsed["filename"])


@app.get("/jobs")
def jobs():
    return {"jobs": storage.list_jobs()}


@app.get("/dna/{job_id}")
def download_dna(job_id: str):
    record = _record_or_404(job_id)
    dna_path = _absolute(record["dna_file"])
    if not dna_path.exists():
        raise HTTPException(status_code=404, detail="DNA file missing on disk")
    return FileResponse(path=str(dna_path), media_type="text/plain", filename=f"{record['original_name']}.dna")


@app.get("/original/{job_id}")
def download_original(job_id: str):
    record = _record_or_404(job_id)
    path = _absolute(record["stored_original"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Original file missing on disk")
    return FileResponse(path=str(path), media_type="application/octet-stream", filename=record["original_name"])


@app.get("/reconstructed/{job_id}")
def download_reconstructed(job_id: str):
    record = _record_or_404(job_id)
    if not record.get("reconstructed"):
        raise HTTPException(status_code=409, detail="Not reconstructed yet")
    path = _absolute(record["reconstructed"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Reconstructed file missing on disk")
    return FileResponse(path=str(path), media_type="application/octet-stream", filename=record["original_name"])
'''

with open('backend/api/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('written')