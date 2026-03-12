import boto3
import json
import botocore.exceptions

# --- Configuration ---
# Please ensure these are correct.
FLOW_IDENTIFIER = ""
FLOW_ALIAS_IDENTIFIER = ""
AWS_REGION = "us-east-1"
# --- End Configuration ---

# Initialize Boto3 client
client_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)

def make_input_payload(text, node_name, is_initial):
    """Creates the correct input payload based on the conversation turn."""
    payload = {
        "nodeName": node_name
    }
    if is_initial:
        # For the initial FlowInputNode, the 'document' output is expected as a STRING
        payload["content"] = {"document": str(text)} 
        payload["nodeOutputName"] = "document" 
    else:
        # For subsequent turns (responding to flowMultiTurnInputRequestEvent),
        # agentInputText expects a document object with mimeType and content.
        payload["content"] = {"document": {"mimeType": "text/plain", "content": str(text)}} 
        payload["nodeInputName"] = "agentInputText" 
    return payload

def process_stream(response_stream):
    """Processes the event stream and returns key information for the turn."""
    node_name_for_next_turn = None
    prompt_for_user = None
    final_answer = None
    completion_reason = None 

    print("\n--- Processing Stream Events ---")
    event_count = 0
    try:
        for event in response_stream:
            event_count += 1
            print(f"\n[EVENT #{event_count}] -> {json.dumps(event, indent=2)}")

            if 'flowOutputEvent' in event:
                content = event['flowOutputEvent'].get('content', {})
                document_content = content.get('document')
                if isinstance(document_content, dict) and 'content' in document_content:
                    final_answer = document_content.get('content')
                elif isinstance(document_content, str):
                    final_answer = document_content 
                else:
                    final_answer = json.dumps(document_content)
                completion_reason = "FLOW_COMPLETED" 

            elif 'flowMultiTurnInputRequestEvent' in event:
                multi_turn_event = event['flowMultiTurnInputRequestEvent']
                doc_content = multi_turn_event['content'].get('document', {})
                if isinstance(doc_content, dict) and 'content' in doc_content:
                     prompt_for_user = doc_content['content']
                elif isinstance(doc_content, str):
                     prompt_for_user = doc_content
                else:
                     prompt_for_user = json.dumps(doc_content)
                
                node_name_for_next_turn = multi_turn_event['nodeName']
                completion_reason = "INPUT_REQUIRED"

            elif 'flowCompletionEvent' in event:
                completion_reason = event['flowCompletionEvent'].get('completionReason')
                print(f"[INFO] Flow Completion Event received with reason: {completion_reason}")
            
    except botocore.exceptions.EventStreamError as e:
        print(f"[ERROR] An EventStreamError occurred while processing the stream: {e}")
        # This error is likely related to the input payload, as previously seen.
        # It's important to capture it here.
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred within process_stream: {e}")
        import traceback
        traceback.print_exc()

    if event_count == 0:
        print("[CRITICAL] The response stream was empty.")
    
    print("--- End of Stream ---")
    return final_answer, prompt_for_user, node_name_for_next_turn, completion_reason

# --- Main Execution Logic ---
try:
    # --- TURN 1 ---
    print("\n\n--- STARTING TURN 1 ---")
    initial_question = "What’s the daily rate for rooms available from June 15 to June 20, 2025?"
    print(f"User Input: '{initial_question}'")
    
    turn1_input_data = make_input_payload(initial_question, "FlowInputNode", is_initial=True)
    
    response1 = client_runtime.invoke_flow(
        flowIdentifier=FLOW_IDENTIFIER,
        flowAliasIdentifier=FLOW_ALIAS_IDENTIFIER,
        inputs=[turn1_input_data]
    )
    
    # *** CRITICAL: Check for executionId immediately after invoke_flow ***
    execution_id = response1.get('executionId')
    if not execution_id:
        print("\n[CRITICAL ERROR] invoke_flow did NOT return an execution ID.")
        print("This often indicates a configuration issue (Flow ID, Alias, Region) or IAM permissions.")
        print("Please check your Bedrock Flow setup and IAM policies carefully.")
        # You might want to print the full response1 here for more debugging info if needed:
        # print(f"Full response1: {json.dumps(response1, indent=2)}")
        exit() # Halt immediately if no execution ID
        
    print(f"\nReceived Execution ID: {execution_id}")
    
    final_answer_t1, prompt1, node_name1, completion_reason_t1 = process_stream(response1.get("responseStream", []))
    
    if final_answer_t1:
        print("\n[SUCCESS] Flow completed in Turn 1 with a final answer.")
        print("Final Answer Text:")
        print(final_answer_t1)
    elif prompt1 and node_name1:
        print(f"\nAgent asks: '{prompt1}'")

        # --- TURN 2 ---
        print("\n\n--- STARTING TURN 2 ---")
        follow_up_answer = "2" # Assuming '2' is a valid response to the prompt
        print(f"User Input: '{follow_up_answer}'")

        turn2_input_data = make_input_payload(follow_up_answer, node_name1, is_initial=False)

        response2 = client_runtime.invoke_flow(
            flowIdentifier=FLOW_IDENTIFIER,
            flowAliasIdentifier=FLOW_ALIAS_IDENTIFIER,
            inputs=[turn2_input_data],
            executionId=execution_id # Use the ID from Turn 1
        )

        print(f"Sent request for Turn 2 with Execution ID: {execution_id}")

        final_answer_t2, _, _, completion_reason_t2 = process_stream(response2.get("responseStream", []))

        print("\n\n--- SCRIPT COMPLETE ---")
        if final_answer_t2:
            print("\n[SUCCESS] Final answer was successfully extracted from the Turn 2 events.")
            print("Final Answer Text:")
            print(final_answer_t2)
        else:
            print(f"\n[FAILURE] Could not extract a final answer from the Turn 2 event stream. Completion Reason: {completion_reason_t2}")
            print("This means the 'flowOutputEvent' was either missing or had an unexpected format, or the flow is still awaiting more input.")
    else:
        print(f"\n[FAILURE] Flow did not complete and did not request further input in Turn 1. Completion Reason: {completion_reason_t1}")
        print("This might indicate an issue with the flow definition or an unexpected completion state.")


except botocore.exceptions.ClientError as e:
    # Catch specific AWS API errors
    print(f"\n--- AWS Client Error Occurred ---")
    print(f"Error Code: {e.response.get('Error', {}).get('Code')}")
    print(f"Error Message: {e.response.get('Error', {}).get('Message')}")
    print("Please check your AWS configuration, credentials, and Bedrock Flow setup.")
except Exception as e:
    print(f"\n--- AN UNEXPECTED PYTHON ERROR OCCURRED ---")
    import traceback
    traceback.print_exc()