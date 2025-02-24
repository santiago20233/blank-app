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
        .profile-container { position: absolute; top: 15px; right: 15px; }
        .profile-icon { background-color: #ff69b4; color: white; padding: 10px; border-radius: 50%; font-size: 18px; font-weight: bold; cursor: pointer; }
    </style>
""", unsafe_allow_html=True)

# ---------------- SIGN-IN SYSTEM ---------------- #

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.user_id = None

# Always show sign-in button or profile icon
if st.session_state.user_logged_in:
    user_doc = db.collection("users").document(st.session_state.user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    
    user_initials = (user_data.get("first_name", "U")[0] + user_data.get("last_name", "N")[0]).upper()
    
    with st.sidebar:
        if st.button(f"🔵 {user_initials} (Profile)"):
            profile_expander = st.expander("User Profile")
            with profile_expander:
                st.write(f"**Name:** {user_data.get('first_name', 'Unknown')} {user_data.get('last_name', '')}")
                st.write(f"**Email:** {user_data.get('email', 'Unknown')}")
                st.write(f"**Baby’s Name:** {user_data.get('baby_name', 'Not Provided')}")
                st.write(f"**Baby’s Birth Date:** {user_data.get('baby_birth_date', 'Not Provided')}")
                st.write(f"**Pregnancy Week:** {user_data.get('pregnancy_weeks', 'Not Provided')}")
                
                if st.button("Log out"):
                    st.session_state.user_logged_in = False
                    st.session_state.user_id = None
                    st.rerun()

else:
    if st.button("Sign in"):
        st.session_state.show_login = True
        st.rerun()

# ---------------- LOGIN FORM ---------------- #

if "show_login" in st.session_state and st.session_state.show_login:
    with st.sidebar:
        st.title("Sign Up / Login")

        first_name = st.text_input("First Name (for sign-up)")
        last_name = st.text_input("Last Name (for sign-up)")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        baby_name = st.text_input("Baby's Name (Optional)")
        baby_birth_date = st.date_input("Baby's Birth Date (Optional)")
        pregnancy_weeks = st.number_input("Pregnancy Week (Optional)", min_value=1, max_value=40, step=1)

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
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "baby_name": baby_name if baby_name else None,
                    "baby_birth_date": str(baby_birth_date) if baby_birth_date else None,
                    "pregnancy_weeks": pregnancy_weeks if pregnancy_weeks > 0 else None,
                    "sign_up_date": firestore.SERVER_TIMESTAMP
                })
                st.success("Account created! Please log in.")
                st.rerun()
            except:
                st.error("Sign-up failed. Try again.")

# ---------------- SUGGESTED QUESTIONS (EXPANDER) ---------------- #
suggested_questions = {
    "👶 Baby Care": [
        "When does the belly button fall off?",
        "When should my baby start doing tummy time?",
        "How do I establish a sleep routine for my newborn?",
        "When is it recommended to introduce solid foods?"
    ],
    "🤱 Postpartum Recovery": [
        "How can I care for my C-section wound?",
        "What should I expect during postpartum recovery?"
    ],
    "🤰 Pregnancy": [
        "How to avoid stretch marks during my pregnancy?",
        "What are the essential vitamins and nutrients I should take?"
    ]
}

with st.expander("💡 Suggested Questions"):
    for category, questions in suggested_questions.items():
        st.markdown(f"**{category}**")
        for question in questions:
            st.markdown(f"- {question}")

# ---------------- DISPLAY FULL CHAT HISTORY ---------------- #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:  
    role_class = "user-message" if message["role"] == "user" else "ai-message"
    st.markdown(f"<div class='chat-container'><div class='chat-bubble {role_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# ---------------- CHAT INPUT ---------------- #

user_input = st.chat_input("Type your question here...")

if user_input:
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

    assistant_reply = f"{response.choices[0].message.content}"
    typing_placeholder.empty()

    st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})

    st.markdown(f"<div class='chat-container'><div class='chat-bubble ai-message'>{assistant_reply}</div></div>", unsafe_allow_html=True)
