import os
import json
import uuid
import boto3
from datetime import datetime
from decimal import Decimal

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

# partition key-->application_id 
TABLE_NAME = os.environ.get('APPLICATION_TABLE', 'mortage_applications') 
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    print(f"Raw input from Bedrock agent: {json.dumps(event)}")

    # 1) Try to extract parameters from "parameters"
    params = {p.get('name'): p.get('value') for p in event.get('parameters', [])}

    # 2) If "parameters" is empty, fallback to requestBody
    if not params and "requestBody" in event:
        props = event.get("requestBody", {}).get("content", {}).get("application/json", {}).get("properties", [])
        params = {p.get("name"): p.get("value") for p in props}
        print("[INFO] Parameters extracted from requestBody fallback.")

    # Print extracted parameters for debugging
    print(f"[DEBUG] Extracted Parameters: {json.dumps(params)}")

    # 3) Parse required fields
    full_name            = params.get("full_name")
    monthly_income       = params.get("monthly_income")
    employment_type      = params.get("employment_type")
    property_value       = params.get("property_value")
    down_payment         = params.get("down_payment")
    preferred_term_years = params.get("preferred_term_years")
    has_existing_loans   = params.get("has_existing_loans")
    citizenship_status   = params.get("citizenship_status")

    required_fields = ["full_name", "monthly_income", "employment_type",
                       "property_value", "down_payment", "citizenship_status"]

    missing = [f for f in required_fields if params.get(f) in [None, ""]]
    if missing:
        result = {"error": f"Missing required fields: {', '.join(missing)}"}
    else:
        try:
            application_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()

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
            table.put_item(Item=item)

            result = {
                "application_id": application_id,
                "created_at": created_at
            }

        except Exception as e:
            result = {"error": str(e)}

    # 4) Format response in Bedrock agent format
    response_body = {
        'application/json': {
            'body': json.dumps(result)
        }
    }

    action_response = {
        'actionGroup':    event.get('actionGroup'),
        'apiPath':        event.get('apiPath'),
        'httpMethod':     event.get('httpMethod'),
        'httpStatusCode': 200,
        'responseBody':   response_body
    }

    api_response = {
        'messageVersion':          '1.0',
        'response':                action_response,
        'sessionAttributes':       event.get('sessionAttributes', {}),
        'promptSessionAttributes': event.get('promptSessionAttributes', {})
    }

    return api_response
