import json
import boto3
from time import sleep

# Redshift Serverless Data API configuration
REGION         = "us-east-1"
WORKGROUP_NAME = "default-workgroup"
DATABASE       = "dev"
SECRET_ARN     = "arn:aws:secretsmanager:us-east-1:127489365181:secret:redshift_secret-E5XN8U"

# Initialize Redshift Data API client
redshift = boto3.client("redshift-data", region_name=REGION)

def lambda_handler(event, context):
    # 1) Log raw Bedrock event
    print("Input from Bedrock agent:", json.dumps(event))
    
    # 2) Extract parameters from agent
    params = { p["name"]: p["value"] for p in event.get("parameters", []) }
    prop_type = params.get("property_type")
    place     = params.get("place_name")
    price     = params.get("price")
    
    # 3) Validate inputs
    if not (prop_type and place and price):
        result = {"error": "Missing required parameters: property_type, place_name, price"}
    else:
        try:
            max_price = float(price)
            
            # 4) SQL with named parameters
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

            # 5) Execute the query
            resp = redshift.execute_statement(
                WorkgroupName=WORKGROUP_NAME,
                Database=DATABASE,
                SecretArn=SECRET_ARN,
                Sql=sql,
                Parameters=[
                    {"name":"pt","value":prop_type},
                    {"name":"pl","value":place},
                    {"name":"pr","value":str(max_price)}
                ]
            )
            stmt_id = resp["Id"]

            # 6) Poll until done
            while True:
                desc = redshift.describe_statement(Id=stmt_id)
                status = desc["Status"]
                if status in ("FINISHED","FAILED","ABORTED"):
                    break
                sleep(1)

            if status != "FINISHED":
                err = desc.get("Error","Unknown error")
                result = {"error": f"Query failed: {err}"}
            else:
                # 7) Fetch results
                out = redshift.get_statement_result(Id=stmt_id)
                cols = [c["name"] for c in out["ColumnMetadata"]]
                listings = []
                for row in out["Records"]:
                    rec = {}
                    for i, fld in enumerate(row):
                        rec[cols[i]] = next(iter(fld.values()))
                    listings.append(rec)
                result = {"listings": listings}

        except Exception as e:
            result = {"error": str(e)}

    # 8) Wrap into Bedrock Agent response format
    response_body = {
        "application/json": {
            "body": json.dumps(result)
        }
    }
    action_response = {
        "actionGroup":      event.get("actionGroup"),
        "apiPath":          event.get("apiPath"),
        "httpMethod":       event.get("httpMethod"),
        "httpStatusCode":   200,
        "responseBody":     response_body
    }
    api_response = {
        "messageVersion":         "1.0",
        "response":               action_response,
        "sessionAttributes":      event.get("sessionAttributes", {}),
        "promptSessionAttributes": event.get("promptSessionAttributes", {})
    }
    return api_response