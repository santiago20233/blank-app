import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from openai import OpenAI

# Load Firebase credentials from Streamlit Secrets
firebase_config = json.loads(st.secrets["firebase"])
cred = credentials.Certificate(firebase_config)

# Initialize Firebase (only if not already initialized)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Firestore Database
db = firestore.client()

# OpenAI API Key (Add it to Streamlit Secrets as well)
openai_api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=openai_api_key)

# User Authentication
st.sidebar.title("Sign Up / Login")

email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

login_btn = st.sidebar.button("Login")
signup_btn = st.sidebar.button("Sign Up")

user_id = None
if login_btn:
    try:
        user = auth.get_user_by_email(email)
        user_id = user.uid
        st.sidebar.success("Logged in successfully!")
    except:
        st.sidebar.error("Invalid credentials.")

if signup_btn:
    try:
        user = auth.create_user(email=email, password=password)
        user_id = user.uid
        db.collection("users").document(user_id).set({
            "email": email,
            "pregnancy_weeks": None,
            "baby_age_months": None
        })
        st.sidebar.success("Account created! Please log in.")
    except:
        st.sidebar.error("Sign-up failed. Try again.")

if not user_id:
    st.stop()

# Load User Data
user_doc = db.collection("users").document(user_id).get()
user_data = user_doc.to_dict()

# Ask Pregnancy or Baby Age if First Time
if user_data["pregnancy_weeks"] is None and user_data["baby_age_months"] is None:
    st.sidebar.subheader("Tell us about your journey")
    pregnancy_weeks = st.sidebar.number_input("How many weeks pregnant are you?", min_value=0, max_value=40, step=1)
    baby_age_months = st.sidebar.number_input("How old is your baby (in months)?", min_value=0, max_value=24, step=1)
    if st.sidebar.button("Save Info"):
        db.collection("users").document(user_id).update({
            "pregnancy_weeks": pregnancy_weeks if pregnancy_weeks > 0 else None,
            "baby_age_months": baby_age_months if baby_age_months > 0 else None
        })
        st.sidebar.success("Information saved! Refresh to see updates.")

# Chat History
chat_ref = db.collection("chats").document(user_id)
chat_doc = chat_ref.get()

if chat_doc.exists:
    chat_history = chat_doc.to_dict()["history"]
else:
    chat_history = [{"role": "system", "content": "You are Fifi, a pregnancy and baby care assistant."}]

# Display Pregnancy Follow-Ups
if user_data["pregnancy_weeks"]:
    st.info(f"Hey! You are now {user_data['pregnancy_weeks']} weeks pregnant! Your baby is growing rapidly.")

if user_data["baby_age_months"]:
    st.info(f"Hey! Your baby is {user_data['baby_age_months']} months old. Make sure to check on vaccinations.")

# Display Chat
st.title("Fifi - Your AI Mommy Assistant")

for message in chat_history[1:]:  # Skip system message
    st.markdown(f"**{message['role'].capitalize()}:** {message['content']}")

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
    chat_ref.set({"history": chat_history})

    st.markdown(f"**Assistant:** {assistant_reply}")

# Set Reminders
st.sidebar.subheader("Set a Reminder")
reminder_text = st.sidebar.text_input("Reminder (e.g., 'Doctor appointment next Monday')")
if st.sidebar.button("Save Reminder"):
    db.collection("users").document(user_id).update({
        "reminders": firestore.ArrayUnion([reminder_text])
    })
    st.sidebar.success("Reminder saved!")
