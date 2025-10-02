# Chromosome 21 Gene API

An AWS Lambda REST API for exploring Ensembl Chromosome 21 gene metadata. The
function exposes lightweight endpoints that follow RESTful conventions and use a
SQLite database automatically seeded from the bundled mart export during cold
starts.

## Features

- Lambda-native REST routing without external web frameworks.
- SQLite persistence managed via SQLAlchemy and seeded on cold start.
- Container image packaging for AWS Lambda.
- Deployment guidance for AWS best practices.

## Getting started

### Prerequisites

- Docker 20.10+
- (Optional) AWS SAM CLI for local testing

### Build the Lambda container image

```bash
docker build -t chromosome21-gene-api .
```

### Invoke locally with AWS SAM

1. Install dependencies into a local virtual environment if you plan to run
   scripts or tests:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run the Lambda function locally:

   ```bash
   sam local invoke --event events/get-genes.json
   ```

   Sample events can be created under an `events/` directory (not committed) to
   emulate API Gateway proxy requests.

### Configuration

The function reads the `DATABASE_URL` environment variable to use an alternative
database connection (for example, an Amazon Aurora cluster). When omitted, it
defaults to the bundled SQLite database file located alongside the code.

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

The repository includes an AWS Lambda handler (`aws_lambda.py`) and a
Lambda-optimised Dockerfile. For a production-ready deployment that follows AWS
best practices, including Infrastructure as Code, CI/CD automation,
observability, and security considerations, see
[docs/aws-deployment.md](docs/aws-deployment.md).
