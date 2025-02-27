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

# Always show sign-in button at the top
if not st.session_state.user_logged_in:
    if st.button("Sign in"):
        st.session_state.show_login = True
        st.rerun()

# ---------------- SUGGESTED QUESTIONS (DROPDOWN) ---------------- #
suggested_questions = {
    "👶 Cuidado del Bebé": [
        "¿Cuándo se cae el cordón umbilical?",
        "¿Cuándo debería empezar mi bebé con el tummy time?",
        "¿Cómo puedo establecer una rutina de sueño para mi recién nacido?",
        "¿Cuándo se recomienda introducir alimentos sólidos?"
    ],
    "🤱 Recuperación Postparto": [
        "¿Cómo puedo cuidar mi herida de cesárea?",
        "¿Qué debo esperar durante la recuperación postparto?"
    ],
    "🤰 Embarazo": [
        "¿Cómo evitar las estrías durante el embarazo?",
        "¿Qué vitaminas y nutrientes son esenciales para mí?"
    ]
}

with st.expander("💡 Preguntas Sugeridas"):
    for category, questions in suggested_questions.items():
        st.markdown(f"**{category}**")
        for question in questions:
            st.markdown(f"- {question}")

# ---------------- CHAT SECTION ---------------- #

st.markdown("<div class='title-container'><p class='title'>fifi</p><p class='subtitle'>Aquí para acompañarte en este hermoso viaje 🤰💖</p></div>", unsafe_allow_html=True)

user_id = st.session_state.user_id if st.session_state.user_logged_in else None
chat_ref = db.collection("chats").document(user_id) if user_id else None

if "chat_history" not in st.session_state:
    if user_id and chat_ref.get().exists:
        st.session_state.chat_history = chat_ref.get().to_dict()["history"]
    else:
        st.session_state.chat_history = [{"role": "system", "content": "Eres Fifi, una asistente de embarazo y cuidado del bebé. Siempre brindas respuestas cálidas, comprensivas y amorosas para acompañar a las mamás en su viaje."}]

# ---------------- DISPLAY CHAT HISTORY ---------------- #
for message in st.session_state.chat_history[1:]:  
    role_class = "user-message" if message["role"] == "user" else "ai-message"
    st.markdown(f"<div class='chat-container'><div class='chat-bubble {role_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# ---------------- CHAT INPUT ---------------- #

user_input = st.chat_input("Escribe tu pregunta aquí...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.markdown(f"<div class='chat-container'><div class='chat-bubble user-message'>{user_input}</div></div>", unsafe_allow_html=True)

    typing_placeholder = st.empty()
    with typing_placeholder:
        st.markdown("<div class='typing-indicator'>Escribiendo...</div>", unsafe_allow_html=True)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.chat_history,
        temperature=0.4,
        max_tokens=600
    )

    assistant_reply = f"{response.choices[0].message.content}"

    # Selección dinámica de artículos relacionados en español
    related_articles = {
        "bebé": [
            {"title": "Cuidado del recién nacido", "url": "https://ejemplo.com/cuidado-bebe", "description": "Consejos esenciales para cuidar a tu bebé en sus primeros meses."}
        ],
        "embarazo": [
            {"title": "Alimentación en el embarazo", "url": "https://ejemplo.com/nutricion-embarazo", "description": "Descubre qué alimentos son más beneficiosos durante el embarazo."}
        ],
        "postparto": [
            {"title": "Recuperación postparto", "url": "https://ejemplo.com/recuperacion-postparto", "description": "Todo lo que necesitas saber para cuidarte después del parto."}
        ]
    }

    selected_articles = []
    for key, articles in related_articles.items():
        if key in user_input.lower():
            selected_articles = articles
            break

    if selected_articles:
        assistant_reply += "\n\n💖 **Artículos recomendados para ti:**"
        for article in selected_articles:
            assistant_reply += f"\n- **[{article['title']}]({article['url']})** – {article['description']}"

    typing_placeholder.empty()
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})

    if user_id:
        chat_ref.set({"history": st.session_state.chat_history})

    st.markdown(f"<div class='chat-container'><div class='chat-bubble ai-message'>{assistant_reply}</div></div>", unsafe_allow_html=True)
