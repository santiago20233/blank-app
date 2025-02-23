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
        .title-container { text-align: center; margin-bottom: 10px; }
        .title { font-size: 36px; font-weight: bold; color: black; text-transform: uppercase; }
        .subtitle { font-size: 18px; font-weight: normal; color: #666; }
        .chat-container { display: flex; flex-direction: column; align-items: center; max-width: 600px; margin: auto; }
        .chat-bubble { padding: 12px; border-radius: 16px; margin: 8px 0; font-size: 16px; width: fit-content; max-width: 80%; }
        .user-message { background-color: #4a90e2; color: white; align-self: flex-end; }
        .ai-message { background-color: #f1f1f1; border: 1px solid #ddd; color: black; align-self: flex-start; }
        .typing-indicator { font-size: 14px; color: #888; font-style: italic; margin-top: 5px; }
        .signin-button { position: absolute; top: 15px; right: 15px; background-color: #ff69b4; color: white; padding: 8px 15px; border-radius: 8px; cursor: pointer; }
    </style>
""", unsafe_allow_html=True)

# ---------------- SIGN-IN SYSTEM ---------------- #

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.user_id = None

# Always show sign-in button at the top
if not st.session_state.user_logged_in:
    if st.button("Sign in"):
        st.session_state.show_login = True
        st.rerun()

# ---------------- LOGIN FORM ---------------- #

if "show_login" in st.session_state and st.session_state.show_login:
    with st.sidebar:
        st.title("Sign Up / Login")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        login_btn = st.button("Login")
        signup_btn = st.button("Sign Up")

        if login_btn:
            try:
                user = auth.get_user_by_email(email)
                st.session_state.user_id = user.uid
                st.session_state.user_logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            except:
                st.error("Invalid credentials.")

        if signup_btn:
            try:
                user = auth.create_user(email=email, password=password)
                st.session_state.user_id = user.uid
                db.collection("users").document(user.uid).set({
                    "email": email,
                    "pregnancy_weeks": None,
                    "baby_age_months": None
                })
                st.success("Account created! Please log in.")
                st.rerun()
            except:
                st.error("Sign-up failed. Try again.")

# ---------------- CHAT SECTION ---------------- #

# Display title & subtitle
st.markdown("<div class='title-container'><p class='title'>FIFI</p><p class='subtitle'>Call me mommy! 🤰</p></div>", unsafe_allow_html=True)

# Retrieve chat history for logged-in users
user_id = st.session_state.user_id if st.session_state.user_logged_in else None
chat_ref = db.collection("chats").document(user_id) if user_id else None

# ---------------- LOCAL CHAT HISTORY FOR LOGGED-OUT USERS ---------------- #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": "You are Fifi, a pregnancy and baby care assistant."}]

# Load chat history from Firestore if logged in
if user_id and chat_ref.get().exists:
    st.session_state.chat_history = chat_ref.get().to_dict()["history"]

# Display chat history (Even if logged out)
for message in st.session_state.chat_history[1:]:  
    role_class = "user-message" if message["role"] == "user" else "ai-message"
    st.markdown(f"<div class='chat-container'><div class='chat-bubble {role_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# ---------------- SUGGESTED QUESTIONS (DROPDOWN) ---------------- #

suggestions = [
    "When should my baby start doing tummy time?",
    "How can I cure my C-section?",
    "When does the belly button fall?",
    "How long after the birth can I shower my baby?",
    "How to avoid stretch marks during my pregnancy?"
]

st.selectbox("💡 Suggested Questions (View Only)", ["Select a question"] + suggestions, index=0, disabled=True)

# ---------------- CHAT INPUT ---------------- #

user_input = st.chat_input("Type your question here...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Display user message immediately
    st.markdown(f"<div class='chat-container'><div class='chat-bubble user-message'>{user_input}</div></div>", unsafe_allow_html=True)

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

    # Save chat history only if user is logged in
    if user_id:
        chat_ref.set({"history": st.session_state.chat_history})

    # Display Fifi's response
    st.markdown(f"<div class='chat-container'><div class='chat-bubble ai-message'>{assistant_reply}</div></div>", unsafe_allow_html=True)
