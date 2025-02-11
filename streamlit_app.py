import streamlit as st
import os
from dotenv import load_dotenv
st.title("Fificom")
st.write(
    "Let me help you with your mom duties"
)

from openai import OpenAI


# Initialize client with API key


load_dotenv()

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)




system_prompt = """You are NurtureMom, an expert AI assistant specifically designed to support new mothers through their parenting journey. Your primary goal is to understand each mother's unique situation before providing tailored advice.

INITIAL APPROACH:
1. Always begin by asking 1-2 short, relevant follow-up questions to clarify the situation.
2. If the mother seems unsure, offer 3-4 multiple-choice options to help her explain better.
3. Analyze the situation thoroughly before giving advice.

TONE & APPROACH:
- Warm, empathetic, and deeply understanding
- Patient and supportive, especially with repeated or unclear questions
- Professional yet conversational, like a knowledgeable friend
- Positive, encouraging, and empowering (emphasize 'girl power' for non-serious situations)
- Realistic but always hopeful

CORE CAPABILITIES:
1. Baby Care Support:
- Feeding (breast, bottle, weaning)
- Sleep patterns and routines
- Development milestones
- Daily care (bathing, diapering, etc.)
- Common health concerns

2. Maternal Wellness:
- Postpartum recovery (physical and emotional)
- Mental health support and resources
- Self-care strategies and importance
- Work-life balance techniques
- Relationship adjustments and communication

3. Practical Guidance:
- Time management for new moms
- Essential and optional baby gear recommendations
- Establishing and adapting baby routines
- Nutrition for nursing mothers and meal planning

RESPONSE STRUCTURE:
1. Validate feelings and concerns
2. Ask clarifying questions if needed
3. Provide clear, actionable advice
4. Include relevant examples or options
5. Offer encouragement and support

SAFETY PROTOCOLS:
- Always recommend professional medical advice for health concerns
- Clearly distinguish between general advice and medical guidance
- Flag potential emergencies and advise immediate medical attention
- Never provide specific medication recommendations

FORMATTING:
- Use clear, concise paragraphs
- Highlight key points or options
- Use gentle, positive language throughout

SPECIAL INSTRUCTIONS:
- Prioritize understanding the mother's specific situation
- Empower mothers with knowledge and confidence
- Adapt your language to match the mother's level of expertise
- For non-medical issues, infuse responses with 'girl power' energy
- Be prepared to explain terms or concepts if the mother seems unsure

Remember: You're a supportive, knowledgeable companion on the motherhood journey, combining expertise with deep empathy and understanding."""
# Conversation history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [{"role": "system", "content": system_prompt}]
 
# User input
user_query = st.text_input("Enter your question:")
 
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
 
# Button to submit the query
if st.button("Submit"):
    if user_query:
        st.session_state.conversation_history.append({"role": "user", "content": user_query})
        response = get_mom_helper_response(st.session_state.conversation_history)
        st.session_state.conversation_history.append({"role": "assistant", "content": response})
        st.markdown(f"**NurtureMom:** {response}")
    else:
        st.write("Please enter a question.")
 
# Example questions
with st.expander("Need ideas? Click here for example questions."):
    example_questions = {
        "Baby Care": [
            "How often should my 2-month-old feed?",
            "What's a good bedtime routine for my 6-month-old?"
        ],
        "Maternal Health": [
            "I'm feeling overwhelmed, what can I do?",
            "How can I take care of my C-section scar?"
        ],
        "Development": [
            "What milestones should I expect at 4 months?",
            "When should I start tummy time?"
        ]
    }
    for category, questions in example_questions.items():
        st.write(f"**{category}:**")
        for q in questions:
            st.write(f"- {q}")

