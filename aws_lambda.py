"""Lambda-native REST API implementation for the Chromosome 21 Gene dataset."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from http import HTTPStatus
from typing import Any, Dict, Iterable, Optional

from sqlalchemy import or_

from database import Gene, SessionLocal, init_db

# Ensure the database exists and is seeded when the Lambda execution environment
# is first created. Subsequent invocations within the same container will reuse
# the initialised state which keeps cold-start latency low.
init_db()


@dataclass
class GeneDTO:
    """Serializable representation of a :class:`Gene` ORM model."""

    gene_stable_id: str
    gene_name: Optional[str]
    gene_description: Optional[str]
    chromosome: Optional[str]
    gene_start: Optional[int]
    gene_end: Optional[int]
    strand: Optional[int]
    gene_type: Optional[str]


def _serialise_gene(model: Gene) -> GeneDTO:
    return GeneDTO(
        gene_stable_id=model.gene_stable_id,
        gene_name=model.gene_name,
        gene_description=model.gene_description,
        chromosome=model.chromosome,
        gene_start=model.gene_start,
        gene_end=model.gene_end,
        strand=model.strand,
        gene_type=model.gene_type,
    )


def _parse_int(value: Optional[str], *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid integer value: {value}") from None


def _respond(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }


def _list_genes(params: Dict[str, str]) -> Dict[str, Any]:
    page = _parse_int(params.get("page"), default=1)
    page_size = _parse_int(params.get("page_size"), default=25)

    if page < 1:
        raise ValueError("page must be >= 1")
    if not 1 <= page_size <= 200:
        raise ValueError("page_size must be between 1 and 200")

    chromosome = params.get("chromosome")
    gene_type = params.get("gene_type")
    search = params.get("search")

    with SessionLocal() as session:
        query = session.query(Gene)
        if chromosome:
            query = query.filter(Gene.chromosome == chromosome)
        if gene_type:
            query = query.filter(Gene.gene_type.ilike(f"%{gene_type}%"))
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Gene.gene_name.ilike(pattern),
                    Gene.gene_description.ilike(pattern),
                )
            )

        total = query.count()
        items: Iterable[Gene] = (
            query.order_by(Gene.gene_start)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        payload = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [asdict(_serialise_gene(item)) for item in items],
        }
    return payload


def _get_gene(gene_id: str) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        gene = session.get(Gene, gene_id)
        if gene is None:
            return None
        return asdict(_serialise_gene(gene))


def _get_gene_by_name(gene_name: str) -> Optional[Dict[str, Any]]:
    with SessionLocal() as session:
        gene = (
            session.query(Gene)
            .filter(Gene.gene_name.is_not(None))
            .filter(Gene.gene_name.ilike(gene_name))
            .order_by(Gene.gene_start)
            .first()
        )
        if gene is None:
            return None
        return asdict(_serialise_gene(gene))


def _extract_segments(event: Dict[str, Any]) -> list[str]:
    proxy = (
        (event.get("pathParameters") or {}).get("proxy")
        or event.get("rawPath")
        or event.get("path")
        or "/"
    )

    if proxy.startswith("/"):
        proxy = proxy[1:]

    stage = (event.get("requestContext") or {}).get("stage")
    if stage and proxy.startswith(stage + "/"):
        proxy = proxy[len(stage) + 1 :]

    if not proxy:
        return []

    return [segment for segment in proxy.split("/") if segment]


def handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """Entry point for AWS Lambda proxy integrations."""

    method = event.get("httpMethod", "GET").upper()
    if method != "GET":
        return _respond(
            HTTPStatus.METHOD_NOT_ALLOWED,
            {"message": "Only HTTP GET is supported."},
        )

    segments = _extract_segments(event)

    if not segments:
        return _respond(HTTPStatus.OK, {"message": "Welcome to Chromosome 21 Gene API"})

    if segments[0] != "genes":
        return _respond(HTTPStatus.NOT_FOUND, {"message": "Resource not found."})

    query_params = event.get("queryStringParameters") or {}

    try:
        if len(segments) == 1:
            return _respond(HTTPStatus.OK, _list_genes(query_params))

        if len(segments) == 2 and segments[1] != "by-name":
            gene = _get_gene(segments[1])
            if gene is None:
                return _respond(HTTPStatus.NOT_FOUND, {"message": "Gene not found."})
            return _respond(HTTPStatus.OK, gene)

        if len(segments) == 3 and segments[1] == "by-name":
            gene = _get_gene_by_name(segments[2])
            if gene is None:
                return _respond(HTTPStatus.NOT_FOUND, {"message": "Gene not found."})
            return _respond(HTTPStatus.OK, gene)
    except ValueError as exc:
        return _respond(HTTPStatus.BAD_REQUEST, {"message": str(exc)})

    return _respond(HTTPStatus.NOT_FOUND, {"message": "Resource not found."})


__all__ = ["handler"]
