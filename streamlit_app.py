import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from openai import OpenAI
import time

# Load Firebase credentials
firebase_config = st.secrets["firebase"]
cred = credentials.Certificate(dict(firebase_config))

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Firestore Database
db = firestore.client()

# OpenAI API Key
openai_api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=openai_api_key)

# ---------------- UI CUSTOMIZATION ---------------- #

st.markdown("""
    <style>
        /* Centering the title */
        .title-container {
            text-align: center;
            margin-bottom: 10px;
        }
        .title {
            font-size: 36px;
            font-weight: bold;
            color: black;
            text-transform: uppercase;
        }
        .subtitle {
            font-size: 18px;
            font-weight: normal;
            color: #666;
        }
        /* Chat bubbles */
        .chat-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            max-width: 600px;
            margin: auto;
        }
        .chat-bubble {
            padding: 12px;
            border-radius: 16px;
            margin: 8px 0;
            font-size: 16px;
            width: fit-content;
            max-width: 80%;
        }
        .user-message {
            background-color: #4a90e2;
            color: white;
            align-self: flex-end;
        }
        .ai-message {
            background-color: #f1f1f1;
            border: 1px solid #ddd;
            color: black;
            align-self: flex-start;
        }
        /* Typing indicator */
        .typing-indicator {
            font-size: 14px;
            color: #888;
            font-style: italic;
            margin-top: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- DISPLAY TITLE & SUBTITLE ---------------- #

st.markdown("<div class='title-container'><p class='title'>FIFI</p><p class='subtitle'>Call me mommy! 🤰</p></div>", unsafe_allow_html=True)

# ---------------- CHAT FUNCTIONALITY ---------------- #

# Retrieve chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": "You are Fifi, a pregnancy and baby care assistant."}]

# Display chat history
for message in st.session_state.chat_history[1:]:  
    role_class = "user-message" if message["role"] == "user" else "ai-message"
    st.markdown(f"<div class='chat-container'><div class='chat-bubble {role_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# ---------------- SUGGESTED QUESTIONS ---------------- #

suggestions = [
    "When should my baby start doing tummy time",
    "How can I cure my C-section",
    "When does the belly button fall",
    "How long after the birth can I shower my baby",
    "How to avoid stretch marks during my pregnancy?"
]

selected_question = st.selectbox("💡 Need ideas? Select a question:", [""] + suggestions)

if selected_question:
    st.session_state["user_input"] = selected_question
    st.rerun()

# ---------------- CHAT INPUT ---------------- #

user_input = st.chat_input("Type your question here...")

if "user_input" in st.session_state and st.session_state["user_input"]:
    user_input = st.session_state["user_input"]
    del st.session_state["user_input"]

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Show typing indicator
    with st.spinner("Fifi is typing..."):
        time.sleep(1.5)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.chat_history,
        temperature=0.4,
        max_tokens=600
    )
    assistant_reply = response.choices[0].message.content

    st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})

    st.markdown(f"<div class='chat-container'><div class='chat-bubble ai-message'>{assistant_reply}</div></div>", unsafe_allow_html=True)
