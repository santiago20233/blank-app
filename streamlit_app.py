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

# Custom CSS for ChatGPT-like UI
st.markdown("""
    <style>
        .title-container {
            text-align: center;
            margin-bottom: 10px;
        }
        .title {
            font-size: 60px;
            font-weight: bold;
            color: #FF69B4; /* Pink color */
            text-transform: lowercase;
        }
        .subtitle {
            font-size: 20px;
            font-weight: normal;
            color: #888;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .chat-bubble {
            padding: 12px;
            border-radius: 16px;
            margin: 8px 0;
            max-width: 80%;
            font-size: 16px;
        }
        .user-message {
            background-color: #4a90e2;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .ai-message {
            background-color: #f1f1f1;
            border: 1px solid #ddd;
            color: black;
            text-align: left;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- LOGIN POPUP (TOAST NOTIFICATION) ---------------- #

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.user_id = None

if "popup_shown" not in st.session_state:
    st.session_state.popup_shown = False

# Show pop-up notification at the top of the screen
if not st.session_state.popup_shown:
    with st.toast("✨ Log in to save chat history & get pregnancy follow-ups!"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Log in / Sign up"):
                st.session_state.show_login = True  # Show login form
        with col2:
            if st.button("Stay logged out"):
                st.session_state.user_logged_in = False
                st.session_state.popup_shown = True  # Dismiss pop-up
                st.rerun()

# ---------------- LOGIN FORM ---------------- #
if "show_login" in st.session_state and st.session_state.show_login:
    st.sidebar.title("Sign Up / Login")

    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    login_btn = st.sidebar.button("Login")
    signup_btn = st.sidebar.button("Sign Up")

    if login_btn:
        try:
            user = auth.get_user_by_email(email)
            st.session_state.user_id = user.uid
            st.session_state.user_logged_in = True
            st.sidebar.success("Logged in successfully!")
            st.rerun()
        except:
            st.sidebar.error("Invalid credentials.")

    if signup_btn:
        try:
            user = auth.create_user(email=email, password=password)
            st.session_state.user_id = user.uid
            db.collection("users").document(user.uid).set({
                "email": email,
                "pregnancy_weeks": None,
                "baby_age_months": None
            })
            st.sidebar.success("Account created! Please log in.")
            st.rerun()
        except:
            st.sidebar.error("Sign-up failed. Try again.")

# ---------------- CHAT SECTION ---------------- #

# Display title & subtitle
st.markdown("<div class='title-container'><p class='title'>fifi</p><p class='subtitle'>call me mommy 🤰</p></div>", unsafe_allow_html=True)

# Check if user is logged in
user_id = st.session_state.user_id if st.session_state.user_logged_in else None

# Retrieve chat history (only if logged in)
chat_ref = db.collection("chats").document(user_id) if user_id else None
chat_history = chat_ref.get().to_dict()["history"] if chat_ref and chat_ref.get().exists else [{"role": "system", "content": "You are Fifi, a pregnancy and baby care assistant."}]

# Display chat
for message in chat_history[1:]:  # Skip system message
    role_class = "user-message" if message["role"] == "user" else "ai-message"
    st.markdown(f"<div class='chat-container'><div class='chat-bubble {role_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# Suggested questions dropdown
with st.expander("💡 Need ideas? Click here for example questions."):
    example_questions = [
        "When should my baby start doing tummy time?",
        "How can I cure my C-section?",
        "When does the belly button fall?",
        "How long after birth can I shower my baby?",
        "How to avoid stretch marks during my pregnancy?"
    ]
    for question in example_questions:
        st.markdown(f"- {question}")

# Chat input
user_input = st.chat_input("Type your question here...")

if user_input:
    chat_history.append({"role": "user", "content": user_input})

    # Get AI Response
    response = client.chat.completions.create(
        model="gpt-4",
        messages=chat_history,
        temperature=0.4,
        max_tokens=600
    )
    assistant_reply = response.choices[0].message.content

    chat_history.append({"role": "assistant", "content": assistant_reply})

    # Save chat history only if logged in
    if user_id:
        chat_ref.set({"history": chat_history})

    # Display AI response
    st.markdown(f"<div class='chat-container'><div class='chat-bubble ai-message'>{assistant_reply}</div></div>", unsafe_allow_html=True)
