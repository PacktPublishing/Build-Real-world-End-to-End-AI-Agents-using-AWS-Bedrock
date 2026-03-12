import streamlit as st
import boto3
import uuid
import json

# ── AWS Clients ────────────────────────────────────────────────────────────────
session = boto3.session.Session()
sts = session.client("sts")
region = session.region_name or "us-east-1"
account_id = sts.get_caller_identity()["Account"]
bedrock = boto3.client("bedrock-agent-runtime", region_name=region)

# ── Agent Configuration ─────────────────────────────────────────────────────────
AGENT_ID = "PGJCAIWRJV"
AGENT_ALIAS_ID = "9RPZ0M5SKC"

# ── Streamlit State Initialization ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # each item: {"role": "user"|"assistant", "content": str}

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ── Page Layout ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AWS Bedrock Chatbot", page_icon="🤖")
st.title("🤖 AWS Bedrock Chatbot")

# Render past conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── User Input ──────────────────────────────────────────────────────────────────
user_input = st.chat_input("Type your message here...")

if user_input:
    # 1) display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # 2) prepare placeholder for assistant streaming response
    placeholder = st.empty()
    with placeholder.chat_message("assistant"):
        # start with an empty message
        streamed_text = ""

    # 3) call Bedrock once
    response = bedrock.invoke_agent(
        inputText=user_input,
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=st.session_state.session_id,
        enableTrace=False,
        endSession=False,
    )
    event_stream = response["completion"]

    # 4) stream chunks into the placeholder
    for event in event_stream:
        if "chunk" in event:
            chunk = event["chunk"]["bytes"].decode("utf-8")
            streamed_text += chunk
            # update the same assistant bubble
            placeholder.write(streamed_text)
        # ignore traces

    # 5) save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": streamed_text})