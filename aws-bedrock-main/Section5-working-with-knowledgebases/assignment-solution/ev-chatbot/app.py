import streamlit as st
import boto3
import json

# Initialize Bedrock Agent Runtime client
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime')

# Configurations
kb_id = ""
model_id = "amazon.nova-lite-v1:0"
model_arn = f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'
max_results = 3

# Prompt template used by Bedrock KB retrieval
default_prompt = """
You are a helpful assistant who helps users addressing questions related to Electric vehicle charging infrastructure.
$search_results$
"""

# Function to call Bedrock Knowledge Base
def call_bedrock_kb(query: str) -> str:
    try:
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
        return response['output']['text']
    except Exception as e:
        return f"Error invoking Bedrock KB: {e}"

# Streamlit UI
st.title("EV Charging Assistant (Bedrock KB Grounded)")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.form(key="chat_form"):
    user_input = st.text_input("You:")
    submitted = st.form_submit_button("Send")

    if submitted and user_input:
        st.session_state.chat_history.append(("User", user_input))

        bot_response = call_bedrock_kb(user_input)
        st.session_state.chat_history.append(("Bot", bot_response))

# Display chat history
st.markdown("### Conversation History")
for speaker, message in st.session_state.chat_history:
    st.markdown(f"**{speaker}:** {message}")