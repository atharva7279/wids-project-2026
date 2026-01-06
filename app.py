import streamlit as st
from google import genai
from google . genai import types
from dotenv import load_dotenv
import os
api_key = os. getenv (" GOOGLE_API_KEY ")
import streamlit as st

import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
import os
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Gemini Clone", layout="centered")
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash-lite"
DATA_FILE = "chat_history.json"

# ---------------- JSON HELPERS ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"interactions": []}

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # File exists but is empty or corrupted
        return {"interactions": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_interaction(query, response):
    data = load_data()
    data["interactions"].append({
        "query": query,
        "response": response,
        "time": datetime.now().isoformat()
    })
    save_data(data)

# ---------------- UI ----------------
st.title("Gemini Clone with locally stored history")
st.caption("check the file chat_history.json to see the history being stored !")

if "chat" not in st.session_state:
    st.session_state.chat = []

# Display current session chat
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Ask anything...")

if user_input:
    # User message
    st.session_state.chat.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Gemini response
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )
        ]
    )

    reply = response.text

    # Assistant message
    st.session_state.chat.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

    # Save to JSON
    save_interaction(user_input, reply)

# ---------------- SIDEBAR ----------------
st.sidebar.header("Saved Chat History")

if st.sidebar.button("Load saved chats"):
    data = load_data()
    for item in data["interactions"]:
        st.sidebar.markdown(
            f"**Q:** {item['query']}\n\n"
            f"**A:** {item['response']}\n\n"
            f"⏱ {item['time']}\n---"
        )