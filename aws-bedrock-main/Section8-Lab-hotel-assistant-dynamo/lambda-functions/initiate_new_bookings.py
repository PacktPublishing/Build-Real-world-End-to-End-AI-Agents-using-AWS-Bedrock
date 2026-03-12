import os
import json
import uuid
import boto3
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Attr

# DynamoDB setup
dynamodb      = boto3.resource('dynamodb')
BOOKING_TABLE = os.environ.get('BOOKING_TABLE', 'booking_details')
ROOM_TABLE    = os.environ.get('ROOM_TABLE',    'room_inventory')
booking_tbl   = dynamodb.Table(BOOKING_TABLE)
room_tbl      = dynamodb.Table(ROOM_TABLE)

def lambda_handler(event, context):
    # 1) Log the raw Bedrock event
    print("Input from Bedrock agent:", json.dumps(event))
    
    # 2) Extract parameters
    params = {p['name']: p['value'] for p in event.get('parameters', [])}
    check_in  = params.get('check_in_date')
    check_out = params.get('check_out_date')
    num_guests= params.get('number_of_guests')
    guest_name= params.get('guest_name')
    email     = params.get('email')
    phone     = params.get('phone')
    room_id   = params.get('room_id')
    
    # 3) Validate inputs
    if not all([check_in, check_out, num_guests, guest_name, email, phone, room_id]):
        result = {"error": "Missing one or more required parameters"}
    else:
        try:
            # parse dates
            d_in  = datetime.strptime(check_in,  "%Y-%m-%d").date()
            d_out = datetime.strptime(check_out, "%Y-%m-%d").date()
            days  = (d_out - d_in).days
            if days <= 0:
                raise ValueError("check_out_date must be after check_in_date")
            
            # convert number_of_guests to int
            num_guests = int(num_guests)
            
            # 4) Fetch room to get price_per_day
            room_resp = room_tbl.get_item(Key={'room_id': room_id})
            room = room_resp.get('Item')
            if not room or 'price_per_day' not in room:
                raise ValueError(f"Room {room_id} not found or missing price_per_day")
            
            price = room['price_per_day']
            # ensure Decimal
            price = Decimal(str(price))
            paid_amount = price * Decimal(days)
            
            # 5) Create booking record
            booking_id   = str(uuid.uuid4())
            booking_date = datetime.utcnow().strftime("%Y-%m-%d")
            booking_item = {
                'booking_id':       booking_id,
                'guest_id':         str(uuid.uuid4()),
                'guest_name':       guest_name,
                'email':            email,
                'phone':            phone,
                'room_id':          room_id,
                'booking_date':     booking_date,
                'check_in_date':    check_in,
                'check_out_date':   check_out,
                'number_of_guests': num_guests,
                'status':           'CONFIRMED',
                'paid_amount':      paid_amount
            }
            booking_tbl.put_item(Item=booking_item)
            
            # 6) Update room availability: shift available_from to check_out_date
            room_tbl.update_item(
                Key={'room_id': room_id},
                UpdateExpression="SET available_from = :new_from",
                ExpressionAttributeValues={':new_from': check_out}
            )
            
            # 7) Build success result
            result = {
                'booking_id':  booking_id,
                'paid_amount': float(paid_amount),
                'status':      'CONFIRMED'
            }
        except Exception as e:
            result = {"error": str(e)}
    
    # 8) Wrap into Bedrock Agent response format
    response_body = {
        'application/json': {
            'body': json.dumps(result)
        }
    }
    print(".......book_rooms Printing response body .......")
    print(response_body)
    
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