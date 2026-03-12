import os
import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

# DynamoDB setup
dynamodb   = boto3.resource('dynamodb')
ROOM_TABLE = os.environ.get('ROOM_TABLE', 'room_inventory')
room_tbl   = dynamodb.Table(ROOM_TABLE)

def lambda_handler(event, context):
    # 1) Log raw input
    print(f"Input from Bedrock agent: {json.dumps(event)}")

    # 2) Extract parameters from agent
    params = { p.get('name'): p.get('value') for p in event.get('parameters', []) }
    start_date = params.get('start_date')
    end_date   = params.get('end_date')
    bed_count  = params.get('bed_count')

    # 3) Validate inputs
    if not (start_date and end_date and bed_count):
        result = {'error': 'Missing parameters: start_date, end_date, bed_count'}
    else:
        try:
            bed_count = int(bed_count)
            # 4) Build filter and scan DynamoDB
            filter_expr = (
                Attr('available_from').lte(start_date) &
                Attr('available_to').gte(end_date) &
                Attr('bed_count').eq(Decimal(bed_count))
            )
            resp  = room_tbl.scan(FilterExpression=filter_expr)
            rooms = resp.get('Items', [])

            # 5) Project requested fields including room_id and price_per_day
            available = []
            for r in rooms:
                price = r.get('price_per_day')
                if isinstance(price, Decimal):
                    price = int(price) if price == price.to_integral() else float(price)
                available.append({
                    'room_id':         r.get('room_id'),
                    'available_from':  r.get('available_from'),
                    'available_to':    r.get('available_to'),
                    'bed_count':       int(r.get('bed_count')),
                    'price_per_day':   price
                })

            result = {'available_rooms': available}
        except Exception as e:
            result = {'error': str(e)}

    # 6) Wrap into Bedrock Agent response format
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
        'messageVersion':         '1.0',
        'response':               action_response,
        'sessionAttributes':      event.get('sessionAttributes', {}),
        'promptSessionAttributes': event.get('promptSessionAttributes', {})
    }

    return api_response