import os
import json
import uuid
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# Load environment variables for the API Key
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="Recipe Making Guide", page_icon="🥘", layout="wide")

# Custom Styling
st.markdown("""
    <style>
        .block-container { padding-bottom: 100px; }
        div[data-testid="stChatInput"] { position: fixed; bottom: 20px; z-index: 99; }
    </style>
""", unsafe_allow_html=True)

# Directory to save chat history
DATA_DIR = "recipe_history"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- Session Management Functions ---
def save_session(session_id, messages):
    with open(f"{DATA_DIR}/{session_id}.json", "w") as f:
        json.dump(messages, f)

def load_session(session_id):
    path = f"{DATA_DIR}/{session_id}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def list_sessions():
    files = os.listdir(DATA_DIR)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(DATA_DIR, x)), reverse=True)
    return [f.replace(".json", "") for f in files if f.endswith(".json")]

# Initialize Session State
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.messages = []

# --- System Instructions (The Logic) ---
system_instruction = """
You are an expert Culinary Assistant. Follow this exact 3-step flow:
1. Ask the user: "What dish would you like to cook today?"
2. Once they name a dish, ask: "Choose a cooking style: Italian, Hindi, Pakistani, or Western Style?"
3. After the style is chosen, provide a full recipe with Ingredients and Step-by-Step Instructions.

RULES:
- Be polite and professional.
- Only provide recipes for the 4 styles mentioned.
- Use Markdown for clear recipe formatting (bolding, lists).
"""

# --- Sidebar ---
with st.sidebar:
    st.title("📖 Saved Recipes")
    if st.button("➕ New Recipe", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    st.write("---")
    for s_id in list_sessions():
        saved_msgs = load_session(s_id)
        user_msgs = [m['content'] for m in saved_msgs if m['role'] == 'user']
        title = user_msgs[0][:25] + "..." if user_msgs else "Empty Chat"
        if st.button(f"🍲 {title}", key=f"hist_{s_id}", use_container_width=True):
            st.session_state.current_session_id = s_id
            st.session_state.messages = saved_msgs
            st.rerun()

# --- Main App UI ---
st.title("🥘 Recipe Making Guide")
st.write("Find recipes in Italian, Hindi, Pakistani, or Western styles.")

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
prompt = st.chat_input("Enter dish name or style here...")

# Groq API Setup
api_key = os.getenv("groq_api") or st.secrets.get("groq_api")
client = Groq(api_key=api_key)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": system_instruction}] + st.session_state.messages,
            model="llama-3.1-8b-instant"
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        save_session(st.session_state.current_session_id, st.session_state.messages)
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")