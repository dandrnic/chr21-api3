FROM public.ecr.aws/lambda/python:3.10

# Install Python dependencies into the Lambda task root.
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application code and dataset.
COPY aws_lambda.py database.py mart_export(3).txt ${LAMBDA_TASK_ROOT}/

# Expose the Lambda handler.
CMD ["aws_lambda.handler"]
