import boto3
import os
import json
import uuid
from datetime import datetime
from decimal import Decimal

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('APPLICATION_TABLE', 'mortage_applications')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        # Extract and parse body
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        # Required fields
        full_name            = body.get("full_name")
        monthly_income       = body.get("monthly_income")
        employment_type      = body.get("employment_type")
        property_value       = body.get("property_value")
        down_payment         = body.get("down_payment")
        preferred_term_years = body.get("preferred_term_years")
        has_existing_loans   = body.get("has_existing_loans")
        citizenship_status   = body.get("citizenship_status")

        required_fields = ["full_name", "monthly_income", "employment_type",
                           "property_value", "down_payment", "citizenship_status"]
        missing = [f for f in required_fields if body.get(f) is None]
        if missing:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Missing required fields: {', '.join(missing)}"})
            }

        application_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        # Build item using Decimal for numeric types
        item = {
            "application_id": application_id,
            "full_name": full_name,
            "monthly_income": Decimal(str(monthly_income)),
            "employment_type": employment_type,
            "property_value": Decimal(str(property_value)),
            "down_payment": Decimal(str(down_payment)),
            "preferred_term_years": int(preferred_term_years) if preferred_term_years else None,
            "has_existing_loans": str(has_existing_loans).lower() == "true",
            "citizenship_status": citizenship_status,
            "created_at": created_at
        }

        # Remove None fields
        item = {k: v for k, v in item.items() if v is not None}

        # Save to DynamoDB
        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "application_id": application_id,
                "created_at": created_at
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }