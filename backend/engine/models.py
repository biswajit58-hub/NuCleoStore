"""SQLAlchemy models for NucleoStore."""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime

from backend.engine.db import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String(32), primary_key=True)
    original_name = Column(String(512), nullable=False)
    stored_original = Column(String(1024), nullable=False)
    dna_file = Column(String(1024), nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    source_bytes = Column(Integer, nullable=False)
    dna_length = Column(Integer, nullable=False)
    ecc = Column(String(16), nullable=False, default="none")
    coding = Column(Integer, nullable=False, default=0)
    reconstructed = Column(String(1024), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "original_name": self.original_name,
            "stored_original": self.stored_original,
            "dna_file": self.dna_file,
            "sha256": self.sha256,
            "source_bytes": self.source_bytes,
            "dna_length": self.dna_length,
            "ecc": self.ecc,
            "coding": self.coding,
            "reconstructed": self.reconstructed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }