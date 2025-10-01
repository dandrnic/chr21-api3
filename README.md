# Chromosome 21 Gene API

A RESTful FastAPI service for exploring Ensembl Chromosome 21 gene metadata. The
service stores its data in a SQLite database that is automatically seeded from
the provided mart export on startup.

## Features

- RESTful endpoints with pagination and filtering for gene metadata.
- SQLite persistence managed via SQLAlchemy.
- Ready-to-run locally with Uvicorn.
- AWS Lambda entrypoint via Mangum for serverless deployments.

## Getting started

### Prerequisites

- Python 3.10+
- `pip`

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running locally

```bash
uvicorn main:app --reload
```

The SQLite database (`chromosome21.sqlite3`) is created in the project root on
first run. The API documentation is available at `http://127.0.0.1:8000/docs`.

### Configuration

Set the `DATABASE_URL` environment variable to use an alternative database
connection (for example, an Amazon Aurora cluster). When omitted, the service
defaults to the bundled SQLite database file.

## REST API

| Method | Endpoint                 | Description                                          |
| ------ | ------------------------ | ---------------------------------------------------- |
| GET    | `/`                      | Health and welcome message.                          |
| GET    | `/genes`                 | Paginated gene list with filter/search parameters.   |
| GET    | `/genes/{gene_stable_id}`| Retrieve a gene by its Ensembl stable identifier.    |
| GET    | `/genes/by-name/{name}`  | Retrieve the first gene matching the given symbol.   |

### Query parameters

- `page` / `page_size`: standard pagination controls.
- `chromosome`: filter by chromosome/scaffold identifier.
- `gene_type`: filter by the reported gene type.
- `search`: case-insensitive search across gene names and descriptions.

## AWS deployment

This project ships with an AWS Lambda handler (`aws_lambda.py`). For a
production-ready deployment that follows AWS best practices, including
Infrastructure as Code, CI/CD automation, observability, and security
considerations, see [docs/aws-deployment.md](docs/aws-deployment.md).
