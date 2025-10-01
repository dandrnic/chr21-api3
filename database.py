"""Database setup and seeding utilities for the Chromosome 21 Gene API."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "mart_export(3).txt"
DATABASE_FILE = BASE_DIR / "chromosome21.sqlite3"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    future=True,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


class Gene(Base):
    """SQLAlchemy model mapping the mart export dataset."""

    __tablename__ = "genes"

    gene_stable_id = Column(String, primary_key=True, index=True)
    gene_name = Column(String, index=True, nullable=True)
    gene_description = Column(String, nullable=True)
    chromosome = Column(String, index=True, nullable=True)
    gene_start = Column(Integer, nullable=True)
    gene_end = Column(Integer, nullable=True)
    strand = Column(Integer, nullable=True)
    gene_type = Column(String, index=True, nullable=True)


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _clean_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _load_dataset() -> Iterable[Gene]:
    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            stable_id = (row.get("Gene stable ID") or "").strip()
            if not stable_id:
                # Skip rows missing a stable identifier because they cannot be queried later.
                continue

            yield Gene(
                gene_stable_id=stable_id,
                gene_name=_clean_str(row.get("Gene name")),
                gene_description=_clean_str(row.get("Gene description")),
                chromosome=_clean_str(row.get("Chromosome/scaffold name")),
                gene_start=_parse_int(row.get("Gene start (bp)")),
                gene_end=_parse_int(row.get("Gene end (bp)")),
                strand=_parse_int(row.get("Strand")),
                gene_type=_clean_str(row.get("Gene type")),
            )


def init_db() -> None:
    """Create tables and seed the database from the source dataset if empty."""

    Base.metadata.create_all(bind=engine)

    if not IS_SQLITE:
        # Assume external databases are already provisioned; avoid auto-seeding.
        return

    dataset = list(_load_dataset())
    if not dataset:
        return

    with SessionLocal() as session:
        has_rows = session.query(Gene).first() is not None
        if has_rows:
            return

        session.add_all(dataset)
        session.commit()


__all__ = [
    "Base",
    "Gene",
    "SessionLocal",
    "engine",
    "init_db",
]
