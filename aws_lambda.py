"""AWS Lambda handler for the Chromosome 21 Gene API."""

from mangum import Mangum

from database import init_db
from main import app

# Warm the SQLite dataset cache during cold starts so the first request served
# by Lambda is fast.
init_db()

# ``lifespan="auto"`` ensures FastAPI startup/shutdown events run correctly in
# the Lambda runtime managed by Mangum.
handler = Mangum(app, lifespan="auto")

__all__ = ["handler"]
