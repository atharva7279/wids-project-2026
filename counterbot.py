import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import random

# ---------------- CONFIG ----------------
st.set_page_config(page_title="CounterBot", layout="centered")

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY not found. Check your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash-lite"

# ---------------- SESSION STATE INIT ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "counter" not in st.session_state:
    st.session_state.counter = 0

if "recent_queries" not in st.session_state:
    st.session_state.recent_queries = []

if "quiz_question" not in st.session_state:
    st.session_state.quiz_question = None

# ---------------- UI ----------------
st.title("CounterBot 🤖")
st.caption("Asks a quiz every 5 questions")

# Display chat history
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- USER INPUT ----------------
user_input = st.chat_input("Ask anything...")

if user_input:
    # Store user message
    st.session_state.chat.append(
        {"role": "user", "content": user_input}
    )

    st.session_state.counter += 1
    st.session_state.recent_queries.append(user_input)

    with st.chat_message("user"):
        st.markdown(user_input)

    # Normal Gemini response
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

# ---------------- QUIZ LOGIC ----------------
if st.session_state.counter == 5:
    quiz_source = random.choice(st.session_state.recent_queries)

    quiz_prompt = (
        "Create a short conceptual quiz question based on the following topic. "
        "Do NOT give the answer.\n\n"
        f"Topic: {quiz_source}"
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

    st.session_state.quiz_question = quiz_response.text

    # Reset counter and buffer
    st.session_state.counter = 0
    st.session_state.recent_queries = []

# ---------------- QUIZ DISPLAY ----------------
if st.session_state.quiz_question:
    st.divider()
    st.subheader("🧠 Quiz Time!")

    st.markdown(st.session_state.quiz_question)

    user_answer = st.text_area("Your answer:")

    if st.button("Submit answer"):
        evaluation_prompt = (
            "You are an examiner.\n\n"
            f"Question: {st.session_state.quiz_question}\n\n"
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

        # Clear quiz after evaluation
        st.session_state.quiz_question = None
