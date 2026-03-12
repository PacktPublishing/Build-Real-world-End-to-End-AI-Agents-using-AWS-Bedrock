import streamlit as st
import boto3
import json

client_bedrock = boto3.client('bedrock-runtime')

def call_bedrock(prompt: str) -> str:
    """
    Calls the Bedrock model and returns the generated response text.
    """
    response = client_bedrock.invoke_model(
        contentType='application/json',
        accept='application/json',
        modelId='cohere.command-light-text-v14',
        body=json.dumps({
            "prompt": prompt,
            "temperature": 0.9,
            "p": 0.75,
            "k": 0,
            "max_tokens": 100
        })
    )
    response_bytes = response['body'].read()
    response_json = json.loads(response_bytes)
    final_response = response_json['generations'][0]['text']
    return final_response

st.title("Bedrock Chatbot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.form(key="chat_form"):
    user_input = st.text_input("You:")
    submitted = st.form_submit_button("Send")
    
    if submitted and user_input:
        st.session_state.chat_history.append(("User", user_input))
    
        try:
            bot_response = call_bedrock(user_input)
        except Exception as e:
            bot_response = f"Error calling Bedrock model: {e}"
        
        st.session_state.chat_history.append(("Bot", bot_response))

st.markdown("### Conversation History")
for speaker, message in st.session_state.chat_history:
    st.markdown(f"**{speaker}:** {message}")