import os
import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')

# partition key-->customer_id
TABLE_NAME = os.environ.get('EXISTING_LOANS_TABLE', 'existing_mortgages')
table = dynamodb.Table(TABLE_NAME)

# Custom encoder for Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def lambda_handler(event, context):
    print(f"Raw input from Bedrock agent: {json.dumps(event)}")

    # 1) Extract parameters from Bedrock event
    params = {p.get('name'): p.get('value') for p in event.get('parameters', [])}

    # 2) Fallback to requestBody if parameters is empty
    if not params and "requestBody" in event:
        props = event.get("requestBody", {}).get("content", {}).get("application/json", {}).get("properties", [])
        params = {p.get("name"): p.get("value") for p in props}
        print("[INFO] Parameters extracted from requestBody fallback.")

    print(f"[DEBUG] Extracted Parameters: {json.dumps(params)}")

    # 3) Validate customer_id
    customer_id = params.get("customer_id")
    if not customer_id:
        result = {"error": "Missing required field: customer_id"}
    else:
        try:
            response = table.query(
                KeyConditionExpression=Key("customer_id").eq(customer_id)
            )
            loans = response.get("Items", [])

            # Extract relevant fields
            result = []
            for item in loans:
                result.append({
                    "mortgage_id":         item.get("mortgage_id"),
                    "bank":                item.get("bank"),
                    "property_type":       item.get("property_type"),
                    "loan_amount":         item.get("loan_amount"),
                    "interest_rate":       item.get("interest_rate"),
                    "term_years":          item.get("term_years"),
                    "status":              item.get("status"),
                    "monthly_payment":     item.get("monthly_payment"),
                    "months_elapsed":      item.get("months_elapsed"),
                    "principal_paid":      item.get("principal_paid"),
                    "remaining_balance":   item.get("remaining_balance"),
                    "last_payment_date":   item.get("last_payment_date"),
                    "missed_payment_flag": item.get("missed_payment_flag")
                })

        except Exception as e:
            result = {"error": str(e)}

    # 4) Return Bedrock-compatible response
    response_body = {
        'application/json': {
            'body': json.dumps(result, cls=DecimalEncoder)
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