import os
import json
import uuid
import boto3
from decimal import Decimal
from datetime import datetime

# DynamoDB setup (make sure these env vars are set on the function)
BOOKING_TABLE = 'booking_details'
ROOM_TABLE    = 'room_inventory'
dynamodb      = boto3.resource('dynamodb')
booking_tbl   = dynamodb.Table(BOOKING_TABLE)
room_tbl      = dynamodb.Table(ROOM_TABLE)

def lambda_handler(event, context):
    try:
        # 1) Read and validate inputs
        body = event if isinstance(event, dict) else {}
        check_in  = body.get('check_in_date')
        check_out = body.get('check_out_date')
        nguests   = body.get('number_of_guests')
        guest_nm  = body.get('guest_name')
        email     = body.get('email')
        phone     = body.get('phone')
        room_id   = body.get('room_id')
        if not all([check_in, check_out, nguests, guest_nm, email, phone, room_id]):
            raise ValueError("Missing one or more required parameters")

        # 2) Parse dates and compute days
        d_in  = datetime.strptime(check_in,  "%Y-%m-%d").date()
        d_out = datetime.strptime(check_out, "%Y-%m-%d").date()
        days  = (d_out - d_in).days
        if days <= 0:
            raise ValueError("check_out_date must be after check_in_date")

        # 3) Convert guests to int
        nguests = int(nguests)

        # 4) Fetch room price
        room = room_tbl.get_item(Key={'room_id': room_id}).get('Item')
        if not room or 'price_per_day' not in room:
            raise ValueError(f"Room {room_id} not found or missing price_per_day")
        price = Decimal(str(room['price_per_day']))
        paid  = price * Decimal(days)

        # 5) Write booking record
        booking_id   = str(uuid.uuid4())
        booking_date = datetime.utcnow().strftime("%Y-%m-%d")
        booking_tbl.put_item(Item={
            'booking_id':       booking_id,
            'guest_id':         str(uuid.uuid4()),
            'guest_name':       guest_nm,
            'email':            email,
            'phone':            phone,
            'room_id':          room_id,
            'booking_date':     booking_date,
            'check_in_date':    check_in,
            'check_out_date':   check_out,
            'number_of_guests': nguests,
            'status':           'CONFIRMED',
            'paid_amount':      paid
        })

        # 6) Update room availability
        room_tbl.update_item(
            Key={'room_id': room_id},
            UpdateExpression="SET available_from = :new",
            ExpressionAttributeValues={':new': check_out}
        )

        # 7) Return success
        return {
            'booking_id':  booking_id,
            'paid_amount': float(paid),
            'status':      'CONFIRMED'
        }

    except Exception as e:
        return { 'error': str(e) }