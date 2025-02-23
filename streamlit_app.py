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
        .title-container {
            text-align: center;
            margin-bottom: 10px;
        }
        .title {
            font-size: 120px; /* Bigger title */
            font-weight: bold;
            color: #FF69B4; /* Pink */
            text-transform: lowercase;
        }
        .subtitle {
            font-size: 25px;
            font-weight: normal;
            color: #888;
        }
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
        .typing-indicator {
            font-size: 14px;
            color: #888;
            font-style: italic;
            margin-top: 5px;
        }
        .signin-button {
            position: absolute;
            top: 15px;
            right: 15px;
            background-color: #ff69b4;
            color: white;
            padding: 8px 15px;
            border-radius: 8px;
            cursor: pointer;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- SIGN-IN MESSAGE (NO POP-UP) ---------------- #

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.user_id = None

# Always show sign-in message at the top
st.markdown('<div class="signin-button">Want reminders & follow-ups? Sign in.</div>', unsafe_allow_html=True)

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
st.markdown("<div class='title-container'><p class='title'>fifi</p><p class='subtitle'>call me mommy 🤰</p></div>", unsafe_allow_html=True)

# Retrieve chat history (only if logged in)
user_id = st.session_state.user_id if st.session_state.user_logged_in else None
chat_ref = db.collection("chats").document(user_id) if user_id else None
chat_history = chat_ref.get().to_dict()["history"] if chat_ref and chat_ref.get().exists else [{"role": "system", "content": "You are Fifi, a pregnancy and baby care assistant."}]

# Display chat
for message in chat_history[1:]:  
    role_class = "user-message" if message["role"] == "user" else "ai-message"
    st.markdown(f"<div class='chat-container'><div class='chat-bubble {role_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# Suggested questions dropdown (Your exact list)
with st.expander("💡 Need ideas? Click a question to ask it."):
    example_questions = [
        "When should my baby start doing tummy time",
        "How can I cure my C-section",
        "When does the belly button fall",
        "How long after the birth can I shower my baby",
        "How to avoid stretch marks during my pregnancy?"
    ]
    for question in example_questions:
        if st.button(question, key=question):
            st.session_state["user_input"] = question
            st.rerun()

# Chat input
user_input = st.chat_input("Type your question here...")

if "user_input" in st.session_state and st.session_state["user_input"]:
    user_input = st.session_state["user_input"]
    del st.session_state["user_input"]

if user_input:
    chat_history.append({"role": "user", "content": user_input})

    # Show typing indicator
    with st.spinner("Fifi is typing..."):
        time.sleep(1.5)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=chat_history,
        temperature=0.4,
        max_tokens=600
    )
    assistant_reply = response.choices[0].message.content

    chat_history.append({"role": "assistant", "content": assistant_reply})

    if user_id:
        chat_ref.set({"history": chat_history})

    st.markdown(f"<div class='chat-container'><div class='chat-bubble ai-message'>{assistant_reply}</div></div>", unsafe_allow_html=True)
