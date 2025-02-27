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
    </style>
""", unsafe_allow_html=True)

# ---------------- SIGN-IN SYSTEM ---------------- #

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.user_id = None

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

        if st.button("Login"):
            try:
                user = auth.get_user_by_email(email)
                st.session_state.user_id = user.uid
                st.session_state.user_logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            except:
                st.error("Invalid credentials.")

        if st.button("Sign Up"):
            try:
                user = auth.create_user(email=email, password=password)
                st.session_state.user_id = user.uid
                db.collection("users").document(user.uid).set({
                    "email": email,
                    "sign_up_date": firestore.SERVER_TIMESTAMP
                })
                st.success("Account created! Please log in.")
                st.rerun()
            except:
                st.error("Sign-up failed. Try again.")

# ---------------- CHAT SECTION ---------------- #

st.markdown("<div class='title-container'><p class='title'>fifi</p><p class='subtitle'>Call me mommy! 🤰</p></div>", unsafe_allow_html=True)

# Retrieve chat history
user_id = st.session_state.user_id if st.session_state.user_logged_in else None
chat_ref = db.collection("chats").document(user_id) if user_id else None

if "chat_history" not in st.session_state:
    if user_id and chat_ref.get().exists:
        st.session_state.chat_history = chat_ref.get().to_dict()["history"]
    else:
        st.session_state.chat_history = [{"role": "system", "content": "You are Fifi, a pregnancy and baby care assistant who always responds in a warm, supportive, and comforting tone. Your goal is to make users feel heard, validated, and cared for in their motherhood journey."}]

# ---------------- CHAT INPUT ---------------- #

user_input = st.chat_input("Talk to fifi...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Display user message
    st.markdown(f"<div class='chat-container'><div class='chat-bubble user-message'>{user_input}</div></div>", unsafe_allow_html=True)

    # Show typing indicator
    typing_placeholder = st.empty()
    with typing_placeholder:
        st.markdown("<div class='typing-indicator'>typing...</div>", unsafe_allow_html=True)

    # Get response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.chat_history,
        temperature=0.4,
        max_tokens=600
    )

    assistant_reply = f"{response.choices[0].message.content}"

    # ---------------- DYNAMIC RELATED ARTICLES ---------------- #

    related_articles = {
        "belly button": ["**[Baby Belly Button Care](https://example.com/belly-button-care)** – Learn how to properly care for your newborn’s belly button."],
        "c-section": ["**[C-Section Recovery Guide](https://example.com/c-section-recovery)** – Tips for healing and taking care of yourself after a C-section."],
        "fever": ["**[Baby Fever Guide](https://example.com/baby-fever)** – How to manage and when to worry about a baby’s fever."],
        "postpartum": ["**[Postpartum Recovery Tips](https://example.com/postpartum-recovery)** – What to expect and how to care for yourself after birth."],
        "solid foods": ["**[Introducing Solids](https://example.com/starting-solids)** – A step-by-step guide for when and how to start solids."],
        "sleep routine": ["**[Newborn Sleep Guide](https://example.com/newborn-sleep)** – Expert tips for better baby sleep."],
        "stretch marks": ["**[Preventing Stretch Marks](https://example.com/stretch-marks)** – How to minimize stretch marks during pregnancy."],
    }

    # Find matching articles based on keywords in user input
    matched_articles = []
    for keyword, articles in related_articles.items():
        if keyword in user_input.lower():
            matched_articles.extend(articles)

    # 🚀 DEBUG PRINTS - REMOVE THIS AFTER TESTING
    print("User Input:", user_input)
    print("Matched Articles:", matched_articles)

    # Append related articles if any matches
    if matched_articles:
        assistant_reply += "\n\n**📚 Related articles:**"
        for article in matched_articles:
            assistant_reply += f"\n- {article}"

    # Remove typing indicator
    typing_placeholder.empty()

    # Save chat history
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
    if user_id:
        chat_ref.set({"history": st.session_state.chat_history})

    # Display assistant response
    st.markdown(f"<div class='chat-container'><div class='chat-bubble ai-message'>{assistant_reply}</div></div>", unsafe_allow_html=True)
