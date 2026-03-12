import os
import json
import boto3
from decimal import Decimal

# EXAMPLE JSON FOR TESTING 
# {
# "product_department": "Women",
# "product_category": "Jumpsuits & Rompers"
# }

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
PRODUCT_TABLE = os.environ.get('PRODUCT_TABLE', 'product_inventory')
product_tbl = dynamodb.Table(PRODUCT_TABLE)

def lambda_handler(event, context):
    """
    Expected event JSON:
    {
      "product_department": "<optional>",
      "product_brand": "<optional>",
      "product_category": "<optional>"
    }
    """
    department = event.get('product_department')
    brand = event.get('product_brand')
    category = event.get('product_category')

    if not (department or brand or category):
        return _response(400, {'error': 'At least one of product_department, product_brand, or product_category is required'})

    # Normalize inputs to lowercase
    department = department.lower() if department else None
    brand = brand.lower() if brand else None
    category = category.lower() if category else None

    try:
        response = product_tbl.scan()
        items = response.get('Items', [])
    except Exception as e:
        return _response(500, {'error': str(e)})

    # Apply case-insensitive filtering in Python
    filtered = []
    for item in items:
        if (
            (not department or item.get('product_department', '').lower() == department) and
            (not brand or item.get('product_brand', '').lower() == brand) and
            (not category or item.get('product_category', '').lower() == category)
        ):
            filtered.append({
                'product_name': item.get('product_name'),
                'product_retail_price': float(item.get('product_retail_price', 0))
            })

    return _response(200, {'matched_products': filtered})

def _response(status_code, body_obj):
    return {
        'statusCode': status_code,
        'body': json.dumps(body_obj)
    }