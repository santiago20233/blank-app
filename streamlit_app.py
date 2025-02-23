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
            font-size: 100px; /* Even Bigger */
            font-weight: bold;
            color: #FF69B4; /* Pink color */
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
        .popup-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            width: 400px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            z-index: 1000;
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

# ---------------- LOGIN POPUP (Centered & Functional) ---------------- #

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.user_id = None

if "popup_shown" not in st.session_state:
    st.session_state.popup_shown = False

if not st.session_state.popup_shown:
    st.markdown("""
    <div class="popup-container">
        <h3>✨ Log in to save chat history & get pregnancy follow-ups!</h3>
        <p>By signing in, you'll get personalized reminders and pregnancy tracking.</p>
        <button class="popup-button popup-login" id="login_btn">Log in / Sign up</button>
        <br>
        <button class="popup-button popup-signup" id="stay_logged_out">Stay logged out</button>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Log in / Sign up"):
        st.session_state.show_login = True
        st.session_state.popup_shown = True
        st.rerun()

    if st.button("Stay logged out"):
        st.session_state.popup_shown = True
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

# Sign-in button (always visible for guests)
if not st.session_state.user_logged_in:
    st.markdown('<div class="signin-button">Sign in</div>', unsafe_allow_html=True)

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

# Chat input
user_input = st.chat_input("Type your question here...")

if user_input:
    chat_history.append({"role": "user", "content": user_input})
    
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
