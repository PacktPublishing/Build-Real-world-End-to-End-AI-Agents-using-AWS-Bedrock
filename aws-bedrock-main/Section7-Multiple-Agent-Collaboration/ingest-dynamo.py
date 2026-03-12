import boto3
import pandas as pd
from decimal import Decimal
from datetime import datetime
import uuid

REGION = 'us-east-1'

# partition key-->customer_id
TABLE_NAME = 'existing_mortgages'

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# Load and preprocess data
df = pd.read_csv('agent-2/existing_mortgages.csv')
df.columns = [col.strip() for col in df.columns]

# Convert float columns to Decimal safely
float_cols = [
    'loan_amount', 'interest_rate', 'monthly_payment',
    'principal_paid', 'remaining_balance'
]
for col in float_cols:
    df[col] = df[col].apply(lambda x: Decimal(str(round(x, 2))))

# Ingest into DynamoDB
with table.batch_writer() as batch:
    for _, row in df.iterrows():
        item = {
            'customer_id': row['customer_id'],
            'mortgage_id': row['mortgage_id'],
            'customer_name': row['customer_name'],
            'bank': row['bank'],
            'property_type': row['property_type'],
            'loan_amount': row['loan_amount'],
            'interest_rate': row['interest_rate'],
            'term_years': int(row['term_years']),
            'start_date': row['start_date'],
            'end_date': row['end_date'],
            'status': row['status'],
            'monthly_payment': row['monthly_payment'],
            'months_elapsed': int(row['months_elapsed']),
            'principal_paid': row['principal_paid'],
            'remaining_balance': row['remaining_balance'],
            'last_payment_date': row['last_payment_date'],
            'missed_payment_flag': row['missed_payment_flag'],
            'ingested_at': datetime.utcnow().isoformat(),
            'record_id': str(uuid.uuid4())  # sort key or unique index
        }
        batch.put_item(Item=item)

print("✅ Ingested existing mortgage loan records into DynamoDB")