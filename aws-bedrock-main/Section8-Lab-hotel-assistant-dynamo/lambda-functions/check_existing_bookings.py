import os
import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

# DynamoDB setup
dynamodb    = boto3.resource('dynamodb')
TABLE_NAME  = os.environ.get('BOOKING_TABLE', 'booking_details')
booking_tbl = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    # 1) Log raw input
    print(f"Input from Bedrock agent: {json.dumps(event)}")
    
    # 2) Extract parameters
    params = {p.get('name'): p.get('value') for p in event.get('parameters', [])}
    email = params.get('email')
    phone = params.get('phone')

    # 2a) Try to parse phone as number
    try:
        phone_num = Decimal(phone)
    except:
        phone_num = None
    
    # 3) Validate presence of at least one identifier
    if not (email or phone_num):
        result = {'error': 'Please provide email and/or phone'}
    else:
        # 4) Build filter expression
        if email and phone_num is not None:
            filt = Attr('email').eq(email) & Attr('phone').eq(phone_num)
        elif email:
            filt = Attr('email').eq(email)
        else:
            filt = Attr('phone').eq(phone_num)
        
        # 5) Query DynamoDB
        try:
            resp = booking_tbl.scan(FilterExpression=filt)
            items = resp.get('Items', [])
            
            # 6) Convert and project output fields
            bookings = []
            for it in items:
                nog = it.get('number_of_guests')
                if isinstance(nog, Decimal):
                    nog = int(nog)
                
                bookings.append({
                    'booking_id':       it.get('booking_id'),
                    'booking_date':     it.get('booking_date'),
                    'check_in_date':    it.get('check_in_date'),
                    'check_out_date':   it.get('check_out_date'),
                    'number_of_guests': nog,
                    'status':           it.get('status')
                })
            result = {'bookings': bookings}
        except Exception as e:
            result = {'error': str(e)}
    
    # 7) Wrap into Bedrock Agent response format
    response_body = {
        'application/json': {
            'body': json.dumps(result)
        }
    }
    action_response = {
        'actionGroup':      event.get('actionGroup'),
        'apiPath':          event.get('apiPath'),
        'httpMethod':       event.get('httpMethod'),
        'httpStatusCode':   200,
        'responseBody':     response_body
    }
    api_response = {
        'messageVersion':         '1.0',
        'response':               action_response,
        'sessionAttributes':      event.get('sessionAttributes', {}),
        'promptSessionAttributes': event.get('promptSessionAttributes', {})
    }
    
    return api_response
