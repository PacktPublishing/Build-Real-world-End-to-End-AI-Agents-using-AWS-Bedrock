import streamlit as st
import boto3
import uuid
import os
import json
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Mortgage Assistant Pro",
    page_icon="🏡",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for a Smart, Serious UI ---
st.markdown("""
<style>
    /* Page background */
    .stApp {
        background-color: #f5f7fa;
    }

    /* Main content container padding */
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 10rem; /* Extra room for fixed input */
        max-width: 800px;
    }

    /* Header banner styling */
    .header-banner {
        background-color: #00334e;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .header-banner h1 {
        color: #ffffff;
        font-size: 2.5rem;
        margin: 0;
        font-weight: 600;
    }

    /* Chat bubble styling */
    div[data-testid="stChatMessageContent"] {
        padding: 1rem 1.25rem;
        border-radius: 20px;
        margin-bottom: 1rem;
        white-space: pre-wrap;
        word-wrap: break-word;
        max-width: 85%;
        font-size: 1rem;
    }
    /* User message bubble (right aligned) */
    div[data-testid="stChatMessage"].st-chat-message-user {
        display: flex;
        justify-content: flex-end;
    }
    div[data-testid="stChatMessage"].st-chat-message-user div[data-testid="stChatMessageContent"] {
        background-color: #cce7ff;
        color: #00334e;
        border-bottom-right-radius: 5px;
    }
    /* Assistant message bubble (left aligned) */
    div[data-testid="stChatMessage"].st-chat-message-assistant {
        display: flex;
        justify-content: flex-start;
    }
    div[data-testid="stChatMessage"].st-chat-message-assistant div[data-testid="stChatMessageContent"] {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #d0d5dd;
        border-bottom-left-radius: 5px;
    }

    /* Hide default avatars */
    .st-chat-avatar {
        display: none !important;
    }
    
    /* Fixed chat input at the bottom */
    .chat-input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #f5f7fa;
        padding: 20px 30px;
        border-top: 1px solid #d0d5dd;
    }
    
    .chat-input-container .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 1rem 1.25rem;
        font-size: 1rem;
        border: 1px solid #b0b7c3;
        background-color: #ffffff;
    }
    
    .chat-input-container .stTextInput > label {
        display: none;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #e3f2f1;
        padding: 2rem 1.5rem;
        border-right: 1px solid #b0bec5;
    }
    .sidebar h2 {
        color: #004d40;
        font-size: 1.8rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .sidebar .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #00796b;
        color: white;
        padding: 0.75rem;
        font-size: 1rem;
        border: none;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
st.markdown("""
<div class="header-banner">
    <h1>Mortgage Assistant Pro</h1>
</div>
""", unsafe_allow_html=True)

# --- Agent Configuration ---
AGENT_ID = ""
AGENT_ALIAS_ID = ""
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

@st.cache_resource
def get_bedrock_client(region: str):
    """Initializes and returns a Boto3 client for Bedrock Agent Runtime."""
    session = boto3.session.Session(region_name=region)
    return session.client('bedrock-agent-runtime')

client = get_bedrock_client(AWS_REGION)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- Display Past Chat Messages ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Function to Invoke Bedrock Agent ---
def invoke_agent(query: str) -> str:
    """Invokes the Bedrock agent and returns the response."""
    try:
        response = client.invoke_agent(
            inputText=query,
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=st.session_state.session_id,
        )
        parts = [e["chunk"]["bytes"].decode("utf-8") for e in response["completion"] if "chunk" in e]
        return "".join(parts).strip()
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
        return "I'm sorry, I encountered an issue. Please try again."

# --- Handle User Input and Agent Response ---
if prompt := st.chat_input("Ask about mortgages...", key="main_chat_input"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = invoke_agent(prompt)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2>Menu</h2>", unsafe_allow_html=True)
    if st.button("🔁 New Chat Session"):
        st.session_state.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("About This App")
    st.info("This intelligent assistant leverages AWS Bedrock to provide expert guidance on mortgage applications and frequently asked questions.")