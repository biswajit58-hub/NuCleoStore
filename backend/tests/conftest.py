"""
conftest.py
-----------
pytest fixtures that isolate every test in its own temporary
SQLite database and storage folders, so tests never touch the
real storage/ directory or nucleostore.db.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """Redirect storage paths and swap the DB engine to a fresh
    SQLite file under tmp_path for this test only."""
    import backend.engine.storage as storage
    import backend.engine.db as db
    from backend.engine.db import Base
    from backend.engine import models  # noqa: F401 - register Job with Base

    # Isolated filesystem paths
    monkeypatch.setattr(storage, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path / "storage")
    monkeypatch.setattr(storage, "ORIGINALS", tmp_path / "storage" / "original_files")
    monkeypatch.setattr(storage, "DNA_DIR", tmp_path / "storage" / "dna_sequences")
    monkeypatch.setattr(storage, "RECONSTRUCTED", tmp_path / "storage" / "reconstructed_files")

    # Fresh DB engine + session for this test
    test_db_path = tmp_path / "test.db"
    test_engine = create_engine(f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False})
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=test_engine)

    monkeypatch.setattr(storage, "SessionLocal", TestSession)

    yield storage