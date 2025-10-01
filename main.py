from __future__ import annotations

from typing import Generator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import Gene, SessionLocal, init_db
from pydantic import BaseModel

app = FastAPI(title="Chromosome 21 Gene API", version="2.0.0")


class GeneRead(BaseModel):
    gene_stable_id: str
    gene_name: Optional[str]
    gene_description: Optional[str]
    chromosome: Optional[str]
    gene_start: Optional[int]
    gene_end: Optional[int]
    strand: Optional[int]
    gene_type: Optional[str]

    class Config:
        orm_mode = True


class GeneListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[GeneRead]


@app.on_event("startup")
def startup_event() -> None:
    """Ensure the SQLite database is initialised before serving requests."""

    init_db()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to Chromosome 21 Gene API"}


@app.get("/genes", response_model=GeneListResponse)
def list_genes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        25,
        ge=1,
        le=200,
        description="Number of genes to return per page (max 200).",
    ),
    chromosome: Optional[str] = Query(
        None, description="Filter genes by chromosome/scaffold name."
    ),
    gene_type: Optional[str] = Query(None, description="Filter genes by gene type."),
    search: Optional[str] = Query(
        None,
        description="Case-insensitive search across gene name and description.",
    ),
    db: Session = Depends(get_db),
) -> GeneListResponse:
    query = db.query(Gene)

    if chromosome:
        query = query.filter(Gene.chromosome == chromosome)
    if gene_type:
        query = query.filter(Gene.gene_type.ilike(f"%{gene_type}%"))
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(Gene.gene_name.ilike(like_pattern), Gene.gene_description.ilike(like_pattern))
        )

    total = query.count()
    items = (
        query.order_by(Gene.gene_start)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return GeneListResponse(total=total, page=page, page_size=page_size, items=items)


@app.get("/genes/{gene_stable_id}", response_model=GeneRead)
def get_gene(gene_stable_id: str, db: Session = Depends(get_db)) -> GeneRead:
    gene = db.get(Gene, gene_stable_id)
    if gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return gene


@app.get("/genes/by-name/{gene_name}", response_model=GeneRead)
def get_gene_by_name(gene_name: str, db: Session = Depends(get_db)) -> GeneRead:
    gene = (
        db.query(Gene)
        .filter(Gene.gene_name.is_not(None))
        .filter(Gene.gene_name.ilike(gene_name))
        .order_by(Gene.gene_start)
        .first()
    )
    if gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return gene
