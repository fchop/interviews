# Setup notes (jhjelte7 fork)

Working notes for running and deploying this fork. The generic instructions are in `README.md`;
this file records the concrete values and commands used for the belief-updating study.
Last updated: 8 October 2026.

## Interview configurations

Defined in `app/parameters.py` (`INTERVIEW_PARAMETERS`):

| Key | Purpose |
|---|---|
| `Qual_Interview_4.0` | earlier adult version |
| `Qual_Interview_4.1` | current adult version |
| `Qual_Interview_4.1_age_{age}` | age-specific variants, e.g. `Qual_Interview_4.1_age_8` |

The configuration formerly called `BELIEF_UPDATING_ADULTS` was renamed to `Qual_Interview` on 27 April 2026;
older notes that use the old name refer to these configs.

## Prerequisites (Windows)

Installed via `winget`: Docker Desktop (needs WSL2), AWS CLI v2, AWS SAM CLI, Python 3.12.

Secrets are read from the environment, never from the repo:

- `OPENAI_API_KEY` as a user environment variable (`setx OPENAI_API_KEY "sk-..."` in a terminal; open a new terminal afterwards).
  `docker-compose.yml` passes it into the container.
- AWS credentials for the `Development` IAM user via `aws configure` (region `eu-central-1`, output `json`).

## Run locally

```bash
cd ~/Documents/GitHub/interviews
docker compose up --build --detach
```

- Health check: `curl http://127.0.0.1:8000/` → `Running!`
- Test interview: http://127.0.0.1:8000/Qual_Interview_4.1/test-session-1
- Transcripts are written to `app/data/<session_id>.json` (gitignored).
- After changing the API key: `docker compose up --detach --force-recreate`.

## Deploy to AWS Lambda

Fixed values:

| Item | Value |
|---|---|
| Region | `eu-central-1` |
| CloudFormation stack | `serverless-interviews` |
| S3 bucket (SAM artifacts) | `jhjelte-interviews-test-2026-4729` |
| DynamoDB table | `interview-sessions` |
| API endpoint | `https://595d5bhbu0.execute-api.eu-central-1.amazonaws.com/Prod/` |

Redeploy after code or prompt changes (Docker Desktop must be running):

```bash
cd ~/Documents/GitHub/interviews
rm -rf .aws-sam
sam build --use-container
sam deploy --parameter-overrides TableName=interview-sessions \
  --no-confirm-changeset --no-fail-on-empty-changeset \
  --s3-bucket jhjelte-interviews-test-2026-4729
```

The endpoint URL stays the same across redeploys. The Lambda's `OPENAI_API_KEY` is set as an environment
variable in the AWS console (Lambda → Configuration → Environment variables) and is preserved by redeploys.

Smoke test:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"route":"next","payload":{"session_id":"test-001","interview_id":"Qual_Interview_4.1","user_message":"I counted the colours."}}' \
  https://595d5bhbu0.execute-api.eu-central-1.amazonaws.com/Prod/
```

Remove test sessions afterwards so they do not mix with real data:

```bash
aws dynamodb delete-item --table-name interview-sessions --key '{"session_id":{"S":"test-001"}}'
```

## Retrieve stored interviews

A local virtual environment `.venv` (gitignored) holds Flask, openai and boto3:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r local_requirements.txt boto3
.venv/Scripts/python aws_retrieve.py --table_name interview-sessions --output_path interviews.csv
```
