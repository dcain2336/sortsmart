"""SortSmart Lambda handler — serves the advisor behind API Gateway.

GET /advise?item=<description>  -> sorting advice as JSON
GET /stats                       -> weekly diversion summary as JSON

When the SORTSMART_TABLE env var is set (deployed via SAM), /advise also
writes the result to DynamoDB. Locally / without the table, it just answers.
"""
import json
import os
from datetime import datetime, timezone

from sortsmart import advise, weekly_summary


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _log_to_dynamodb(item, category):
    table_name = os.environ.get("SORTSMART_TABLE")
    if not table_name:
        return False
    try:
        import boto3  # only needed when deployed
        table = boto3.resource("dynamodb").Table(table_name)
        table.put_item(Item={
            "pk": "log",
            "sk": datetime.now(timezone.utc).isoformat(),
            "item": item,
            "category": category,
        })
        return True
    except Exception:
        return False


def lambda_handler(event, context=None):
    path = (event.get("path") or "").rstrip("/") or "/"
    params = event.get("queryStringParameters") or {}

    if path.endswith("/advise"):
        item = (params.get("item") or "").strip()
        if not item:
            return _response(400, {"error": "missing ?item= query parameter"})
        result = advise(item)
        logged = _log_to_dynamodb(result["item"], result["category"])
        result["logged_to_dynamodb"] = logged
        return _response(200, result)

    if path.endswith("/stats"):
        return _response(200, weekly_summary())

    return _response(404, {
        "error": "unknown route",
        "routes": ["GET /advise?item=<description>", "GET /stats"],
    })
