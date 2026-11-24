# AWS infrastructure (planned deployment)

`template.yaml` is an AWS SAM template for the cloud side of Introspect. It is **not deployed yet**;
we will deploy it on hack day using the team's AWS credits.

| Service | Used for |
|---|---|
| Amazon Bedrock (Claude Haiku) + Bedrock Guardrails | Writes the daily brief from privacy-gateway facts; Guardrails block medical claims |
| AWS Lambda + API Gateway (HTTP API) | Serverless Introspect API (`api.main.handler` via Mangum) |
| Amazon Cognito | User sign-in; JWT authorizer on the API |
| Amazon DynamoDB | Consent ledger: every consent change, auditable |
| Amazon EventBridge Scheduler | Triggers the 07:00 IST daily brief job |
| Amazon S3 + AWS KMS | Opt-in encrypted backups, 90-day expiry |
| Amazon CloudWatch | Logs and metrics (default for Lambda) |

```bash
sam build -t infra/template.yaml
sam deploy --guided            # region with Bedrock access, e.g. us-east-1
```

Before deploying, enable access to the Claude Haiku model in the Bedrock console and (optionally)
create a guardrail with a denied topic "medical diagnosis", then pass its id as `BedrockGuardrailId`.
