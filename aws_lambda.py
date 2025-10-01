"""AWS Lambda handler for the Chromosome 21 Gene API."""

from mangum import Mangum

from main import app, load_genes


# Warm the pandas dataset cache during cold starts so the first request served
# by Lambda is fast.
load_genes()

# ``lifespan="auto"`` ensures FastAPI startup/shutdown events run correctly in
# the Lambda runtime managed by Mangum.
handler = Mangum(app, lifespan="auto")

__all__ = ["handler"]
