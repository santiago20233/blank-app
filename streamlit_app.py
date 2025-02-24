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
        .title { font-size: 50px; font-weight: bold; color: #ff69b4; text-transform: uppercase; }
        .subtitle { font-size: 18px; font-weight: normal; color: #666; }
        .chat-container { display: flex; flex-direction: column; align-items: center; max-width: 600px; margin: auto; }
        .chat-bubble { padding: 12px; border-radius: 16px; margin: 8px 0; font-size: 16px; width: fit-content; max-width: 80%; }
        .user-message { background-color: #4a90e2; color: white; align-self: flex-end; }
        .ai-message { background-color: #f1f1f1; border: 1px solid #ddd; color: black; align-self: flex-start; }
        .typing-indicator { font-size: 14px; color: #888; font-style: italic; margin-top: 5px; }
        .auth-buttons { display: flex; justify-content: center; gap: 10px; margin-bottom: 10px; }
        .auth-button { background-color: #ff69b4; color: white; padding: 8px 15px; border-radius: 8px; cursor: pointer; font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

# ---------------- SIGN-IN SYSTEM ---------------- #

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.user_id = None

# Sign In / Sign Up buttons at the top
col1, col2 = st.columns([1, 1])

with col1:
    if not st.session_state.user_logged_in and st.button("Sign Up", key="signup_btn"):
        st.session_state.show_signup = True
        st.session_state.show_login = False
        st.rerun()

with col2:
    if not st.session_state.user_logged_in and st.button("Log In", key="login_btn"):
        st.session_state.show_login = True
        st.session_state.show_signup = False
        st.rerun()

# ---------------- LOGIN FORM ---------------- #

if "show_login" in st.session_state and st.session_state.show_login:
    with st.sidebar:
        st.title("Welcome Back! 👋")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        login_btn = st.button("Log In")

        if login_btn:
            try:
                user = auth.get_user_by_email(email)
                st.session_state.user_id = user.uid
                st.session_state.user_logged_in = True
                st.success("Logged in successfully!")
                st.session_state.show_login = False
                st.rerun()
            except:
                st.error("Invalid email or password. Try again.")

# ---------------- SIGNUP FORM ---------------- #

if "show_signup" in st.session_state and st.session_state.show_signup:
    with st.sidebar:
        st.title("Create an Account 🎉")
        
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        baby_name = st.text_input("Baby's Name (Optional)")
        pregnancy_weeks = st.number_input("Pregnancy Week (Optional)", min_value=1, max_value=40, step=1)
        baby_birth_date = st.date_input("Baby's Birth Date (Optional)")
        
        signup_btn = st.button("Sign Up")

        if signup_btn:
            try:
                user = auth.create_user(email=email, password=password)
                st.session_state.user_id = user.uid
                db.collection("users").document(user.uid).set({
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "baby_name": baby_name if baby_name else None,
                    "pregnancy_weeks": pregnancy_weeks if pregnancy_weeks > 0 else None,
                    "baby_birth_date": str(baby_birth_date) if baby_birth_date else None,
                    "sign_up_date": firestore.SERVER_TIMESTAMP
                })
                st.success("Account created! Please log in.")
                st.session_state.show_signup = False
                st.rerun()
            except:
                st.error("Sign-up failed. Try again.")

# ---------------- DISPLAY TITLE ---------------- #
if st.session_state.user_logged_in:
    user_doc = db.collection("users").document(st.session_state.user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    st.markdown(f"<p class='title'>Hi, {user_data.get('first_name', 'User')}! 👋</p>", unsafe_allow_html=True)
else:
    st.markdown("<div class='title-container'><p class='title'>fifi</p><p class='subtitle'>Call me mommy! 🤰</p></div>", unsafe_allow_html=True)

# ---------------- SUGGESTED QUESTIONS (DROPDOWN) ---------------- #
suggested_questions = [
    "When does the belly button fall off?",
    "When should my baby start doing tummy time?",
    "How do I establish a sleep routine for my newborn?",
    "When is it recommended to introduce solid foods?",
    "How can I care for my C-section wound?",
    "What should I expect during postpartum recovery?",
    "How to avoid stretch marks during my pregnancy?",
    "What are the essential vitamins and nutrients I should take?"
]

selected_question = st.selectbox("💡 Suggested Questions", ["Select a question..."] + suggested_questions)
if selected_question and selected_question != "Select a question...":
    user_input = selected_question

# ---------------- CHAT INPUT ---------------- #

if user_input := st.chat_input("Type your question here..."):
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    st.markdown(f"<div class='chat-container'><div class='chat-bubble user-message'>{user_input}</div></div>", unsafe_allow_html=True)

    typing_placeholder = st.empty()
    with typing_placeholder:
        st.markdown("<div class='typing-indicator'>typing...</div>", unsafe_allow_html=True)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.chat_history,
        temperature=0.4,
        max_tokens=600
    )

    assistant_reply = response.choices[0].message.content

    typing_placeholder.empty()

    st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})

    st.markdown(f"<div class='chat-container'><div class='chat-bubble ai-message'>{assistant_reply}</div></div>", unsafe_allow_html=True)
