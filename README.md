# SortSmart — know which bin it goes in

Household waste advisor for the **Environmental Hacks** hackathon (WeMakeDevs × AWS, Bharat Builds Tour) — **Track 03: Waste and Energy**.

Most recycling fails at the bin: one greasy pizza box or plastic bag in the wrong stream contaminates the whole batch. SortSmart answers the question everyone asks standing over the trash — *"which bin does this go in?"* — with the reasoning, so people learn the rules instead of guessing.

## What it does

- **Advise:** describe any household item, get the right stream — recycle, compost, e-waste, hazardous, donate, reuse, or landfill — plus *why* and a practical tip. 60+ items in the knowledge base, tuned for the tricky cases (greasy pizza box → compost, plastic bags → store drop-off not curbside, thermal receipts → landfill).
- **Lambda API:** the same advisor served as a serverless HTTP API (`GET /advise?item=…`, `GET /stats`).
- **Weekly tracker:** log what you sort, see your household diversion rate — the % of waste kept out of landfill.

## Run it

```bash
python3 demo.py          # end-to-end demo, 14 checks, exits 0
python3 -m pytest tests/ # unit tests (needs pytest)
```

Try the advisor directly:

```bash
python3 -c "
from sortsmart import advise
for q in ['greasy pizza box', 'AA battery', 'old jacket']:
    a = advise(q); print(a['emoji'], a['label'], '-', a['item'])"
```

## Where AWS fits

This project is built on **AWS SAM (Serverless Application Model)** — the open-source tool from AWS for defining serverless apps as code:

- `template.yaml` is a real SAM template: a Lambda function (`SortSmartFunction`) behind API Gateway (HTTP API) with a DynamoDB table (`sortsmart-weekly-log`, pay-per-request) for the diversion log.
- `lambda/handler.py` is the Lambda handler — it serves API Gateway proxy events and writes to DynamoDB when the `SORTSMART_TABLE` env var is set (injected by the template).
- Verified with the SAM CLI: `sam build` packages the function cleanly (see demo video).

Deploy path (needs an AWS account — free tier covers it): `sam deploy --guided`.

## Project layout

| Path | What |
|---|---|
| `sortsmart/knowledge.py` | 60+ item waste-stream knowledge base |
| `sortsmart/advisor.py` | matching + advice engine |
| `sortsmart/tracker.py` | weekly diversion log + rate |
| `lambda/handler.py` | Lambda handler (API Gateway + DynamoDB) |
| `template.yaml` | SAM template (Lambda + API Gateway + DynamoDB) |
| `demo.py` | end-to-end demo, exits 0 |
| `tests/` | unit tests |

## AI tools used

Built with AI coding assistance (Muse) — code written, tested, and reviewed with an AI pair programmer.

## Notes for judges

- New repo, created during the event window (Oct 8–11, 2026).
- The demo video shows the advisor, the Lambda handler running locally, and `sam build` with the AWS SAM CLI.
