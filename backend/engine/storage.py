"""
storage.py
----------
Manages the on-disk layout and the database records for each job.

Folder layout (relative to project root):
    storage/original_files/<job_id>/<original_filename>
    storage/dna_sequences/<job_id>/<original_filename>.dna
    storage/reconstructed_files/<job_id>/<original_filename>

Job records live in SQLite (storage/nucleostore.db) via SQLAlchemy.
"""

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.engine.db import SessionLocal, init_db, PROJECT_ROOT as DB_PROJECT_ROOT
from backend.engine.models import Job
from backend.engine.pipeline import encode_file, decode_file


PROJECT_ROOT = DB_PROJECT_ROOT
STORAGE_ROOT = PROJECT_ROOT / "storage"
ORIGINALS = STORAGE_ROOT / "original_files"
DNA_DIR = STORAGE_ROOT / "dna_sequences"
RECONSTRUCTED = STORAGE_ROOT / "reconstructed_files"


init_db()


def _portable_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _ensure_dirs():
    for d in (ORIGINALS, DNA_DIR, RECONSTRUCTED):
        d.mkdir(parents=True, exist_ok=True)


def _abs_path(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


def store_and_encode(source_file: str | Path, original_name: str | None = None,
                     ecc: bool = False) -> dict:
    _ensure_dirs()
    source_file = Path(source_file)
    if not source_file.is_file():
        raise FileNotFoundError(f"Not a file: {source_file}")

    name = original_name or source_file.name
    job_id = uuid.uuid4().hex
    job_dir_original = ORIGINALS / job_id
    job_dir_dna = DNA_DIR / job_id
    job_dir_original.mkdir(parents=True, exist_ok=True)
    job_dir_dna.mkdir(parents=True, exist_ok=True)

    stored_original = job_dir_original / name
    shutil.copy2(source_file, stored_original)

    dna_path = job_dir_dna / (name + ".dna")
    result = encode_file(stored_original, dna_path, ecc=ecc)

    job = Job(
        job_id=job_id,
        original_name=name,
        stored_original=_portable_path(stored_original),
        dna_file=_portable_path(dna_path),
        sha256=result["sha256"],
        source_bytes=result["source_bytes"],
        dna_length=result["dna_length"],
        ecc="rep3" if ecc else "none",
        coding=1 if ecc else 0,
        created_at=datetime.now(timezone.utc),
    )

    session = SessionLocal()
    try:
        session.add(job)
        session.commit()
        session.refresh(job)
        return job.to_dict()
    finally:
        session.close()


def reconstruct(job_id: str) -> dict:
    _ensure_dirs()
    session = SessionLocal()
    try:
        job = session.query(Job).filter(Job.job_id == job_id).one_or_none()
        if job is None:
            raise KeyError(f"No job with id {job_id}")

        dna_path = _abs_path(job.dna_file)
        out_dir = RECONSTRUCTED / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / job.original_name

        result = decode_file(dna_path, out_path, expected_sha256=job.sha256)

        job.reconstructed = _portable_path(out_path)
        job.coding = result.get("coding", job.coding)
        session.commit()
        session.refresh(job)

        data = job.to_dict()
        data["reconstructed_result"] = result
        return data
    finally:
        session.close()


def list_jobs() -> list[dict]:
    session = SessionLocal()
    try:
        jobs = session.query(Job).order_by(Job.created_at.desc()).all()
        return [j.to_dict() for j in jobs]
    finally:
        session.close()


def get_job(job_id: str) -> dict | None:
    session = SessionLocal()
    try:
        job = session.query(Job).filter(Job.job_id == job_id).one_or_none()
        return job.to_dict() if job else None
    finally:
        session.close()