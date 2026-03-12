import boto3
import pandas as pd
from decimal import Decimal

REGION = 'us-east-1'
BOOKING_TABLE = 'booking_details'
ROOM_TABLE    = 'room_inventory'

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name=REGION)

# Load CSVs
df_rooms    = pd.read_csv('data/room_inventory.csv')
df_bookings = pd.read_csv('data/booking_details.csv')

# Batch‑write Room Inventory with new price_per_day
room_tbl = dynamodb.Table(ROOM_TABLE)
with room_tbl.batch_writer() as batch:
    for _, r in df_rooms.iterrows():
        batch.put_item(Item={
            'room_id':        r['room_id'],
            'room_type':      r['room_type'],
            'bed_count':      Decimal(int(r['bed_count'])),
            'available_from': r['available_from'],
            'available_to':   r['available_to'],
            'price_per_day':  Decimal(str(r['price_per_day']))
        })
print("✅ Ingested room_inventory with price_per_day")

# Batch‑write Booking Details with renamed paid_amount
booking_tbl = dynamodb.Table(BOOKING_TABLE)
with booking_tbl.batch_writer() as batch:
    for _, b in df_bookings.iterrows():
        batch.put_item(Item={
            'booking_id':       b['booking_id'],
            'guest_id':         b['guest_id'],
            'guest_name':       b['guest_name'],
            'email':            b['email'],
            'phone':            b['phone'],
            'booking_date':     b['booking_date'],
            'check_in_date':    b['check_in_date'],
            'check_out_date':   b['check_out_date'],
            'room_id':          b['room_id'],
            'number_of_guests': Decimal(int(b['number_of_guests'])),
            'status':           b['status'],
            'paid_amount':      Decimal(str(b['paid_amount']))
        })
print("✅ Ingested booking_details with paid_amount")