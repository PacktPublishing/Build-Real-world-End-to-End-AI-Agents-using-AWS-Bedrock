import os
import json
import boto3
from decimal import Decimal


# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
PRODUCT_TABLE = os.environ.get('PRODUCT_TABLE', 'product_inventory')
product_tbl = dynamodb.Table(PRODUCT_TABLE)

def lambda_handler(event, context):
    # 1) Log raw input
    print(f"Input from Bedrock agent: {json.dumps(event)}")

    # 2) Extract parameters from agent
    params = { p.get('name'): p.get('value') for p in event.get('parameters', []) }
    department = params.get('product_department')
    brand      = params.get('product_brand')
    category   = params.get('product_category')

    # 3) Validate at least one parameter
    if not (department or brand or category):
        result = {'error': 'At least one of product_department, product_brand, or product_category is required'}
    else:
        # Normalize inputs to lowercase for case-insensitive filtering
        department = department.lower() if department else None
        brand      = brand.lower() if brand else None
        category   = category.lower() if category else None

        try:
            # 4) Scan entire table and filter in Python
            resp = product_tbl.scan()
            items = resp.get('Items', [])
            matched = []

            for item in items:
                if (
                    (not department or item.get('product_department', '').lower() == department) and
                    (not brand or item.get('product_brand', '').lower() == brand) and
                    (not category or item.get('product_category', '').lower() == category)
                ):
                    price = item.get('product_retail_price')
                    if isinstance(price, Decimal):
                        price = int(price) if price == price.to_integral() else float(price)
                    matched.append({
                        'product_name': item.get('product_name'),
                        'product_retail_price': price
                    })

            result = {'matched_products': matched}
        except Exception as e:
            result = {'error': str(e)}

    # 5) Wrap in Bedrock Agent format
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