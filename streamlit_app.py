import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from openai import OpenAI

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

# Custom CSS for better UI (ChatGPT style pop-up, aesthetic chat)
st.markdown("""
    <style>
        .title-container {
            text-align: center;
            margin-bottom: 10px;
        }
        .title {
            font-size: 50px;
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
        .popup-container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            width: 400px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        }
        .popup-button {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }
        .popup-login {
            background-color: black;
            color: white;
        }
        .popup-signup {
            background-color: white;
            color: black;
            border: 1px solid black;
        }
        .popup-guest {
            color: #888;
            text-decoration: underline;
            cursor: pointer;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- LOGIN POPUP ---------------- #

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.user_id = None

if not st.session_state.user_logged_in:
    st.markdown("""
    <div class="popup-container">
        <h3>Thanks for trying Fifi</h3>
        <p>Log in or sign up to get **reminders, follow-ups, and pregnancy tracking**.</p>
        <button class="popup-button popup-login" onclick="window.location.reload()">Log in</button>
        <button class="popup-button popup-signup" onclick="window.location.reload()">Sign up</button>
        <p class="popup-guest" onclick="window.location.reload()">Stay logged out</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------------- LOGIN FORM ---------------- #
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
with st.expander("Need ideas? Click here for example questions."):
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
