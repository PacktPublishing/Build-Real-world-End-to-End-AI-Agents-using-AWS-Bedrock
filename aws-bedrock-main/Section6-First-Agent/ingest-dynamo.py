import boto3
import pandas as pd
from decimal import Decimal
import uuid

REGION = 'us-east-1'
INVENTORY_TABLE = 'product_inventory'

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name=REGION)

df_inventory = pd.read_csv('datasets/inventory_items.csv')
df_inventory.columns = [col.strip() for col in df_inventory.columns]

inventory_tbl = dynamodb.Table(INVENTORY_TABLE)
with inventory_tbl.batch_writer() as batch:
    for idx, row in df_inventory.iterrows():
        created_at = row['created_at']
        unique_suffix = str(uuid.uuid4())

        item = {
            'product_id': str(row['product_id']),
            'created_at_uuid': f"{created_at}#{unique_suffix}",
            'created_at': created_at,
            'product_category': row['product_category'],
            'product_name': row['product_name'],
            'product_brand': row['product_brand'],
            'product_retail_price': Decimal(str(row['product_retail_price'])),
            'product_department': row['product_department']
        }

        if pd.notnull(row['sold_at']):
            item['sold_at'] = row['sold_at']

        batch.put_item(Item=item)

print("✅ Ingested inventory_items into inventory_details")