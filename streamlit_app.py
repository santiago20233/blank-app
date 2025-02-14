import streamlit as st
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Inject custom CSS for better UI
st.markdown("""
    <style>
        /* Background */
        .stApp {
            background-color: #f7f7f7;
        }
        
        /* Chat bubbles */
        .chat-bubble {
            padding: 12px;
            border-radius: 16px;
            margin: 8px 0;
            max-width: 75%;
            font-size: 16px;
        }

        /* User messages (light blue) */
        .user-message {
            background-color: #4a90e2;
            color: white;
            margin-left: auto;
            text-align: right;
        }

        /* AI messages (light grey) */
        .ai-message {
            background-color: #ffffff;
            border: 1px solid #ddd;
            color: black;
            text-align: left;
        }

        /* Typing indicator */
        .typing-indicator {
            font-size: 16px;
            color: #888;
            font-style: italic;
            animation: dots 1.5s infinite;
        }

        @keyframes dots {
            0% {content: ".";}
            33% {content: "..";}
            66% {content: "...";}
            100% {content: ".";}
        }

        /* Centering messages */
        .chat-container {
            display: flex;
            width: 100%;
        }

        /* Prevent long messages from stretching too much */
        .stMarkdown {
            word-wrap: break-word;
        }

        /* Title styling */
        .title-container {
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# App title and introduction
st.markdown("<div class='title-container'><h1>Fificom</h1><p>Ask away, mama! I got you.</p></div>", unsafe_allow_html=True)

# System prompt definition
system_prompt = """You are NurtureMom, an expert AI assistant specifically designed to support new mothers through their parenting journey. Your primary goal is to understand each mother's unique situation before providing tailored advice."""

# Initialize chat history in session state
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [{"role": "system", "content": system_prompt}]

# Function to get response from OpenAI
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

# Display chat messages with refined formatting
for message in st.session_state.conversation_history[1:]:  # Skip system message
    if message["role"] == "user":
        # User message on the right (blue)
        st.markdown(f"""
        <div class="chat-container" style="justify-content: flex-end;">
            <div class="chat-bubble user-message">
                {message['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # AI response on the left (light grey)
        st.markdown(f"""
        <div class="chat-container" style="justify-content: flex-start;">
            <div class="chat-bubble ai-message">
                {message['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# User input for new message
if user_input := st.chat_input("Type your message here..."):
    # Add user message to history
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    
    # Display user message on the right (blue)
    st.markdown(f"""
    <div class="chat-container" style="justify-content: flex-end;">
        <div class="chat-bubble user-message">
            {user_input}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show typing indicator
    typing_placeholder = st.empty()
    with typing_placeholder:
        st.markdown("""
        <div class="chat-container" style="justify-content: flex-start;">
            <div class="chat-bubble ai-message typing-indicator">
                Typing...
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Simulate a small delay to make it feel natural
    time.sleep(1.5)

    # Get response from AI
    response = get_mom_helper_response(st.session_state.conversation_history)

    # Remove typing indicator
    typing_placeholder.empty()

    # Add AI response to history
    st.session_state.conversation_history.append({"role": "assistant", "content": response})

    # Display AI response on the left (light grey)
    st.markdown(f"""
    <div class="chat-container" style="justify-content: flex-start;">
        <div class="chat-bubble ai-message">
            {response}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Example questions for inspiration
with st.expander("Need ideas? Click here for example questions."):
    example_questions = {
        "Baby Care": [
            "How often should my 2-month-old feed?",
            "How long does it take for the belly button to fall?"
        ],
        "Maternal Health": [
            "I'm feeling overwhelmed, what can I do?",
            "How can I take care of my C-section scar?"
        ],
        "Development": [
            "How to combine breast milk with formula?",
            "When should I start tummy time?"
        ]
    }
    for category, questions in example_questions.items():
        st.write(f"**{category}:**")
        for q in questions:
            st.write(f"- {q}")
