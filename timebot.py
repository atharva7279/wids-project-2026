import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
import os
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
st.set_page_config(page_title="TimeBot", layout="centered")

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY not found. Check your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash-lite"
DATA_FILE = "timebot_history.json"
QUIZ_DELAY = timedelta(minutes=10)

# ---------------- JSON HELPERS ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"interactions": []}

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"interactions": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def save_interaction(query):
    data = load_data()
    data["interactions"].append({
        "query": query,
        "time": datetime.now().isoformat(),
        "quizzed": False
    })
    save_data(data)

# ---------------- SESSION STATE ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "active_quiz" not in st.session_state:
    st.session_state.active_quiz = None

# ---------------- UI ----------------
st.title("TimeBot ⏰")
st.caption("Quizzes you 10 minutes after a question is asked")

# Display chat
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- USER INPUT ----------------
user_input = st.chat_input("Ask anything...")

if user_input:
    st.session_state.chat.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

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

    st.session_state.chat.append(
        {"role": "assistant", "content": reply}
    )

    with st.chat_message("assistant"):
        st.markdown(reply)

    save_interaction(user_input)

# ---------------- TIME-BASED QUIZ CHECK ----------------
data = load_data()
now = datetime.now()

for item in data["interactions"]:
    asked_time = datetime.fromisoformat(item["time"])

    if not item["quizzed"] and now - asked_time >= QUIZ_DELAY:
        quiz_prompt = (
            "Create a short conceptual quiz question based on the following topic. "
            "Do NOT give the answer.\n\n"
            f"Topic: {item['query']}"
        )

        quiz_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=quiz_prompt)]
                )
            ]
        )

        st.session_state.active_quiz = {
            "question": quiz_response.text,
            "topic": item["query"]
        }

        item["quizzed"] = True
        save_data(data)
        break

# ---------------- QUIZ UI ----------------
if st.session_state.active_quiz:
    st.divider()
    st.subheader("🧠 Quiz Time!")

    st.markdown(st.session_state.active_quiz["question"])

    user_answer = st.text_area("Your answer:")

    if st.button("Submit answer"):
        evaluation_prompt = (
            "You are an examiner.\n\n"
            f"Topic: {st.session_state.active_quiz['topic']}\n\n"
            f"Question: {st.session_state.active_quiz['question']}\n\n"
            f"Student Answer: {user_answer}\n\n"
            "Decide whether the answer is correct or incorrect. "
            "Start your response with either 'Correct:' or 'Incorrect:' "
            "and then give a brief explanation."
        )

        evaluation_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=evaluation_prompt)]
                )
            ]
        )

        st.markdown("### Evaluation")
        st.markdown(evaluation_response.text)

        st.session_state.active_quiz = None
