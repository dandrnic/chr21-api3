# AWS deployment guide

This guide outlines a production-ready path for deploying the Chromosome 21 Gene
API to AWS following common industry practices. Although the application uses a
local SQLite database for convenience, the recommended production architecture
replaces SQLite with a managed relational database such as Amazon Aurora Serverless
(MySQL/PostgreSQL compatible) to guarantee durability and scalability.

## 1. Recommended architecture

```
API Gateway (REST) -> AWS Lambda (container image) -> Amazon RDS/Aurora
                                   |-> Amazon CloudWatch Logs & Metrics
                                   |-> AWS X-Ray (optional tracing)
```

Additional services:

- **Amazon S3** for storing deployment artifacts.
- **AWS Secrets Manager** for database credentials and API secrets.
- **Amazon VPC** with private subnets for database access and optional VPC
  connectivity from Lambda (via VPC configuration) if using an RDS instance.

## 2. Infrastructure as Code (IaC)

Use AWS SAM or AWS CDK to manage infrastructure. Below is a minimal SAM template
snippet defining API Gateway, Lambda (container image), and environment variables:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Chromosome 21 Gene API

Globals:
  Function:
    Timeout: 30
    MemorySize: 512
    Tracing: Active
    Environment:
      Variables:
        DATABASE_URL: postgresql+psycopg2://{username}:{password}@{host}:{port}/{db}

Resources:
  GeneApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      ImageUri: <account-id>.dkr.ecr.<region>.amazonaws.com/chromosome21:latest
      Events:
        ApiGateway:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

Adjust `DATABASE_URL` for your chosen engine. Store the actual credentials in
Secrets Manager and inject them using SAM/CloudFormation parameters.

## 3. Build & packaging pipeline

1. **Continuous Integration (CI):**
   - Run unit tests (`pytest`), linting, and type checks on each commit.
   - Build the deployment artifact using Docker to ensure parity with Lambda's
     Amazon Linux runtime.

2. **Artifact packaging:**
   ```bash
   sam build --use-container
   sam package --s3-bucket <artifact-bucket> --output-template-file packaged.yaml
   ```

3. **Continuous Deployment (CD):**
   - Deploy to staging using `sam deploy --template-file packaged.yaml` (SAM) or
     `cdk deploy` (CDK) after pushing the Docker image to Amazon ECR.
   - Promote to production via approval workflows in your CI/CD tool (GitHub
     Actions, AWS CodePipeline, GitLab CI, etc.).

## 4. Database migration strategy

1. Use SQLAlchemy's Alembic migrations to manage schema changes.
2. Run migrations as part of your deployment pipeline (e.g., a one-off Lambda or
   AWS Step Functions task prior to shifting traffic).
3. Seed data by running a separate job that loads the mart export into the RDS
   instance using the same logic as `database.init_db`, adjusted for the managed
   database connection string.

## 5. Observability & operations

- **Logging:** CloudWatch Logs is automatically populated by Lambda. Configure
  structured logging for easier analysis.
- **Metrics:** Use CloudWatch metrics and alarms for error rates, latency, and
  throttling. Consider creating custom metrics for query counts or dataset size.
- **Tracing:** Enable AWS X-Ray for distributed tracing across API Gateway and
  Lambda.
- **Dashboards:** Build CloudWatch dashboards or integrate with third-party
  observability platforms (Datadog, New Relic) as needed.

## 6. Security best practices

- Enforce least-privilege IAM roles for Lambda (access only to Secrets Manager,
  CloudWatch, and database resources required).
- Rotate credentials stored in Secrets Manager regularly.
- Enable AWS WAF on API Gateway for protection against common web attacks.
- Require HTTPS only and configure throttling/quotas on API Gateway.
- Use AWS Shield Advanced if compliance or threat models require it.

## 7. Cost optimisation tips

- Use provisioned concurrency only for latency-sensitive production traffic; rely
  on on-demand for lower environments.
- Choose Aurora Serverless v2 or RDS with autoscaling to adapt to load patterns.
- Set CloudWatch alarms to detect anomalous cost spikes.

## 8. Local parity & testing

- Use Docker Compose with LocalStack to emulate AWS services for integration
  tests.
- Run contract tests against staging endpoints before promoting to production.
- Version your OpenAPI specification and share with consumers to prevent breaking
  changes.

## 9. Deployment checklist

- [ ] OpenAPI spec updated and communicated to API consumers.
- [ ] Database migrations applied.
- [ ] Lambda artifact built and uploaded to S3.
- [ ] Infrastructure stack deployed via SAM/CDK.
- [ ] Smoke tests executed against staging.
- [ ] Monitoring and alarms validated.

Following these practices will help ensure the API is secure, observable, and
scalable when deployed on AWS.
