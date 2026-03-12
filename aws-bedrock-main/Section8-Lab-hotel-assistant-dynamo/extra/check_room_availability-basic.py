import os
import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
ROOM_TABLE = os.environ.get('ROOM_TABLE', 'room_inventory')
room_tbl   = dynamodb.Table(ROOM_TABLE)

def lambda_handler(event, context):
    """
    Expected event JSON:
    {
      "start_date": "YYYY-MM-DD",
      "end_date":   "YYYY-MM-DD",
      "bed_count":  <integer>
    }
    """
    start_date = event.get('start_date')
    end_date   = event.get('end_date')
    bed_count  = event.get('bed_count')

    if not (start_date and end_date and bed_count):
        return _response(400, {'error': 'Missing parameters: start_date, end_date, bed_count'})
    try:
        bed_count = int(bed_count)
    except ValueError:
        return _response(400, {'error': 'bed_count must be an integer'})

    # Filter: available_from ≤ start_date AND available_to ≥ end_date AND bed_count == requested
    filter_expr = (
        Attr('available_from').lte(start_date) &
        Attr('available_to').gte(end_date) &
        Attr('bed_count').eq(Decimal(bed_count))
    )

    try:
        scan_result = room_tbl.scan(FilterExpression=filter_expr)
        rooms = scan_result.get('Items', [])
    except Exception as e:
        return _response(500, {'error': str(e)})

    # Build output with only the requested fields
    available = [
        {
            'available_from': r['available_from'],
            'available_to':   r['available_to'],
            'bed_count':      int(r['bed_count'])
        }
        for r in rooms
    ]

    return _response(200, {'available_rooms': available})

def _response(status_code, body_obj):
    return {
        'statusCode': status_code,
        'body': json.dumps(body_obj)
    }
