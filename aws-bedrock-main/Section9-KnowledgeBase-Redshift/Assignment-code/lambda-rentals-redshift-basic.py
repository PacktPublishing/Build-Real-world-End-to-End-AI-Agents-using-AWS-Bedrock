import json
import boto3
from time import sleep

# Redshift Serverless Data API configuration
REGION         = "us-east-1"
WORKGROUP_NAME = "default-workgroup"
DATABASE       = "dev"
SECRET_ARN     = "arn:aws:secretsmanager:us-east-1:127489365181:secret:redshift-serverless-secret-ti0q1Y"

# Initialize Redshift Data API client
redshift = boto3.client("redshift-data", region_name=REGION)

def lambda_handler(event, context):
    print("Input from Bedrock agent:", json.dumps(event))
    
    # Extract parameters
    params = { p["name"]: p["value"] for p in event.get("parameters", []) }
    prop_type = params.get("property_type")
    place     = params.get("place_name")
    price     = params.get("price")

    try:
        if not (prop_type and place and price):
            raise ValueError("Missing required parameters: property_type, place_name, price")
        
        max_price = float(price)
        sql = """
            SELECT
              description,
              CAST(price AS VARCHAR) || ' ' || currency AS price_with_currency,
              place_name,
              country_name
            FROM rental_listings
            WHERE property_type = :pt
              AND place_name    = :pl
              AND price        <= :pr
            LIMIT 50;
        """

        resp = redshift.execute_statement(
            WorkgroupName=WORKGROUP_NAME,
            Database=DATABASE,
            SecretArn=SECRET_ARN,
            Sql=sql,
            Parameters=[
                {"name": "pt", "value": prop_type},
                {"name": "pl", "value": place},
                {"name": "pr", "value": str(max_price)}
            ]
        )
        stmt_id = resp["Id"]

        # Poll until the statement completes
        while True:
            desc = redshift.describe_statement(Id=stmt_id)
            status = desc["Status"]
            if status in ("FINISHED", "FAILED", "ABORTED"):
                break
            sleep(1)

        if status != "FINISHED":
            err = desc.get("Error", "Unknown error")
            raise RuntimeError(f"Query failed: {err}")

        out = redshift.get_statement_result(Id=stmt_id)
        cols = [c["name"] for c in out["ColumnMetadata"]]
        listings = []
        for row in out["Records"]:
            rec = {}
            for i, fld in enumerate(row):
                rec[cols[i]] = next(iter(fld.values()))
            listings.append(rec)

        return {
            "statusCode": 200,
            "body": json.dumps({"listings": listings})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }