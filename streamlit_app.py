import streamlit as st
import os
import time
import firebase_admin
from firebase_admin import credentials, auth, firestore
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")  # Ensure you add your Firebase credentials JSON
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Function to sign up users
def signup(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        return user.uid
    except Exception as e:
        return None

# Function to log in users
def login(email, password):
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except Exception as e:
        return None

# User Authentication
st.sidebar.header("User Login")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")
login_btn = st.sidebar.button("Login")
signup_btn = st.sidebar.button("Sign Up")

user_id = None
if login_btn:
    user_id = login(email, password)
    if user_id:
        st.sidebar.success("Logged in successfully!")
    else:
        st.sidebar.error("Invalid credentials.")

elif signup_btn:
    user_id = signup(email, password)
    if user_id:
        st.sidebar.success("Account created successfully! Please log in.")
    else:
        st.sidebar.error("Sign-up failed. Try again.")

if not user_id:
    st.stop()

# Fetch user data from Firestore
def get_user_data(user_id):
    doc_ref = db.collection("users").document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return {}

user_data = get_user_data(user_id)

# System prompt definition
system_prompt = """You are Fifi, an expert AI assistant specifically designed to support new mothers through their parenting journey. 
You remember the user's child's name and refer to them personally. If a mother asks for help, such as her child having a fever, you not only provide immediate advice but also follow up later to check on the child and offer further assistance. 
If the user is pregnant and tells you how many weeks they are, you provide updates like 'Your baby is now the size of a melon, and their lungs are starting to develop,' or 'It’s normal to start feeling nausea or back pain at this stage.' You may also suggest relevant products that help with their condition.
You act as a reminder for vaccinations (e.g., 'Your baby is 2 months old, it's time for XYZ vaccine') and allow users to set custom reminders (e.g., 'Next week I have a doctor's appointment' – you remind them when it's due).
Additionally, every time you respond, you provide links to related topics for more information and ask if they would like additional information or suggested questions related to their inquiry."""

# Fetch user-specific chat history
def get_chat_history(user_id):
    chat_ref = db.collection("chats").document(user_id)
    chat = chat_ref.get()
    return chat.to_dict().get("history", []) if chat.exists else [{"role": "system", "content": system_prompt}]

# Save chat history
def save_chat_history(user_id, history):
    db.collection("chats").document(user_id).set({"history": history})

# Load chat history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = get_chat_history(user_id)

# Function to get AI response
def get_mom_helper_response(conversation_history):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=conversation_history,
            temperature=0.4,
            max_tokens=600,
            presence_penalty=0.6,
            frequency_penalty=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Display chat messages
for message in st.session_state.conversation_history[1:]:
    st.markdown(f"**{message['role'].capitalize()}:** {message['content']}")

# User input
if user_input := st.chat_input("Type your message here..."):
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    response = get_mom_helper_response(st.session_state.conversation_history)
    st.session_state.conversation_history.append({"role": "assistant", "content": response})
    save_chat_history(user_id, st.session_state.conversation_history)
    st.markdown(f"**Assistant:** {response}")

# Automated reminders and follow-ups
if user_data.get("pregnancy_weeks"):
    st.info(f"Hey {user_data.get('name', 'Mom')}, you are now {user_data['pregnancy_weeks']} weeks pregnant! Your baby is developing rapidly.")

if user_data.get("baby_age_months"):
    st.info(f"Hey {user_data.get('name', 'Mom')}, your baby is now {user_data['baby_age_months']} months old! Remember to schedule vaccinations and check-ups.")

# Allow users to set reminders
reminder_text = st.text_input("Set a reminder (e.g., 'Doctor appointment next Monday')")
if st.button("Save Reminder"):
    db.collection("users").document(user_id).update({"reminders": firestore.ArrayUnion([reminder_text])})
    st.success("Reminder saved!")
