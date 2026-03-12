import json
import boto3

bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime')

kb_id = "9ODLPMFP4V"
model_id = "amazon.nova-lite-v1:0"
model_arn = f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'
max_results = 3

default_prompt = """
You are a helpful assistant who helps users addressing questions related to AWS Cloud. Only refer to the provided data 
while responding to the questions. 
$search_results$
"""

def lambda_handler(event, context):
    print("Incoming event:", json.dumps(event))

    try:
        if event.get("body"):
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        query = body.get("query")
        if not query:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'query' in request"})
            }

        response = bedrock_agent_runtime_client.retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_id,
                    'modelArn': model_arn,
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': max_results
                        }
                    },
                    'generationConfiguration': {
                        'promptTemplate': {
                            'textPromptTemplate': default_prompt
                        }
                    }
                }
            }
        )

        generated_text = response['output']['text']

        return {
            "statusCode": 200,
            "body": json.dumps({"answer": generated_text})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }