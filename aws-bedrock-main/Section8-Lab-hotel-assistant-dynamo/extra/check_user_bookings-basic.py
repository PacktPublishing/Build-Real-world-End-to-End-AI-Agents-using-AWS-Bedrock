import os
import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('BOOKING_TABLE', 'booking_details')
booking_tbl = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Expects event JSON with one or both:
      {
        "email": "user@example.com",
        "phone": "+971501234567"
      }
    Returns only booking_date, number_of_guests, check_out_date, and booking_id.
    """
    email = event.get('email')
    phone = event.get('phone')
    if not (email or phone):
        return _response(400, {"error": "Please provide email and/or phone"})

    # Build filter
    if email and phone:
        filt = Attr('email').eq(email) & Attr('phone').eq(phone)
    elif email:
        filt = Attr('email').eq(email)
    else:
        filt = Attr('phone').eq(phone)

    # Scan table
    try:
        resp = booking_tbl.scan(FilterExpression=filt)
        items = resp.get('Items', [])
    except Exception as e:
        return _response(500, {"error": str(e)})

    # Convert Decimal → int and pick only the four fields
    results = []
    for it in items:
        # Convert number_of_guests from Decimal to int
        nog = it.get('number_of_guests')
        nog = int(nog) if isinstance(nog, Decimal) else nog

        results.append({
            'booking_id':       it.get('booking_id'),
            'booking_date':     it.get('booking_date'),
            'check_out_date':   it.get('check_out_date'),
            'number_of_guests': nog
        })

    return _response(200, {"bookings": results})


def _response(status, body_obj):
    return {
        "statusCode": status,
        "body": json.dumps(body_obj)
    }