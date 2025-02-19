import streamlit as st
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Inject custom CSS for better UI
st.markdown("""
    <style>
        .stApp { background-color: #f7f7f7; }
        .chat-bubble {
            padding: 12px;
            border-radius: 16px;
            margin: 8px 0;
            max-width: 75%;
            font-size: 16px;
            word-wrap: break-word;
        }
        .user-message { background-color: #4a90e2; color: white; margin-left: auto; text-align: right; }
        .ai-message { background-color: #ffffff; border: 1px solid #ddd; color: black; text-align: left; }
        .typing-indicator { font-size: 16px; color: #888; font-style: italic; }
        .chat-container { display: flex; width: 100%; }
        .title-container { text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# App title
st.markdown("<div class='title-container'><h1>Fifi</h1><p>Call me mommy!</p></div>", unsafe_allow_html=True)

# System prompt definition
system_prompt = """You are Fifi, an expert AI assistant specifically designed to support new mothers through their parenting journey. 
You remember the user's child's name and refer to them personally. If a mother asks for help, such as her child having a fever, you not only provide immediate advice but also follow up later to check on the child and offer further assistance. 
If the user is pregnant and tells you how many weeks they are, you provide updates like 'Your baby is now the size of a melon, and their lungs are starting to develop,' or 'It’s normal to start feeling nausea or back pain at this stage.' You may also suggest relevant products that help with their condition.
You act as a reminder for vaccinations (e.g., 'Your baby is 2 months old, it's time for XYZ vaccine') and allow users to set custom reminders (e.g., 'Next week I have a doctor's appointment' – you remind them when it's due).
Additionally, every time you respond, you provide links to related topics for more information and ask if they would like additional information or suggested questions related to their inquiry."""

# Initialize chat history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [{"role": "system", "content": system_prompt}]

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
auto_scroll_placeholder = st.empty()

for message in st.session_state.conversation_history[1:]:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-container" style="justify-content: flex-end;">
            <div class="chat-bubble user-message">
                {message['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-container" style="justify-content: flex-start;">
            <div class="chat-bubble ai-message">
                {message['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# User input
typing_placeholder = st.empty()
if user_input := st.chat_input("Type your message here..."):
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    
    # Display user message
    st.markdown(f"""
    <div class="chat-container" style="justify-content: flex-end;">
        <div class="chat-bubble user-message">
            {user_input}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show typing indicator dynamically based on expected response time
    typing_placeholder.markdown("""
    <div class="chat-container" style="justify-content: flex-start;">
        <div class="chat-bubble ai-message typing-indicator">
            Typing...
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Dynamic delay based on input length
    time.sleep(min(max(len(user_input) / 10, 1), 3))  # Min 1s, max 3s

    # Get AI response
    response = get_mom_helper_response(st.session_state.conversation_history)
    typing_placeholder.empty()
    st.session_state.conversation_history.append({"role": "assistant", "content": response})
    
    # Display AI response
    st.markdown(f"""
    <div class="chat-container" style="justify-content: flex-start;">
        <div class="chat-bubble ai-message">
            {response}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-scroll to latest message
    auto_scroll_placeholder.empty()
