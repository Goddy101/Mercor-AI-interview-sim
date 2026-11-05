# interfaces/ui_interviewer.py
import streamlit as st
import asyncio
import sys
import plotly.graph_objects as go
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parent.parent))
from agents.mercor_interviewer.state_graph import build_interview_graph, InterviewState

st.set_page_config(page_title="Mercor-Prep | Principal AI Screener", page_icon="⚡", layout="wide")

# --- CUSTOM PREMIUM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { color: #00FF41 !important; font-family: 'Courier New', monospace; }
    .stChatMessage { background-color: #1A1C23; border-radius: 5px; border-left: 3px solid #00FF41; }
    .stProgress > div > div > div > div { background-color: #00FF41; }
    .red-flag { color: #FF4B4B; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def run_async(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

def init_session_state():
    if "graph" not in st.session_state:
        st.session_state.graph = build_interview_graph()
    if "interview_state" not in st.session_state:
        st.session_state.interview_state = InterviewState(
            context="", history=[], evaluations=[], turn_count=0, max_turns=3, current_question=""
        )
    if "interview_started" not in st.session_state:
        st.session_state.interview_started = False
    if "interview_completed" not in st.session_state:
        st.session_state.interview_completed = False

init_session_state()

st.title("⚡ Principal Engineer Screener Engine")
st.markdown("_Adversarial Technical Interview Simulator_")

with st.sidebar:
    st.header("1. Target Architecture")
    uploaded_file = st.file_uploader("Upload ARCHITECTURE_AUDIT.md", type=["md", "txt"])
    
    if uploaded_file and not st.session_state.interview_started:
        st.session_state.interview_state["context"] = uploaded_file.getvalue().decode("utf-8")
        if st.button("Initialize Hostile Audit", type="primary"):
            st.session_state.interview_started = True
            with st.spinner("Analyzing architecture topology..."):
                new_state = run_async(st.session_state.graph.ainvoke(st.session_state.interview_state))
                st.session_state.interview_state.update(new_state)
            st.rerun()

if st.session_state.interview_started and not st.session_state.interview_completed:
    st.header("2. Live Audit Session")
    
    # Display Chat History
    for msg in st.session_state.interview_state["history"]:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            
    # --- DUAL INPUT: TEXT OR VOICE ---
    col_text, col_voice = st.columns([3, 1])
    
    with col_text:
        text_input = st.chat_input("Defend your architecture by typing...")
        
    with col_voice:
        audio_input = st.audio_input("Or speak your defense")

    # Determine which input triggered
    user_input = None
    if text_input:
        user_input = text_input
    elif audio_input:
        with st.spinner("Transcribing your voice response via Whisper..."):
            # Import llm here or at the top of the file: from core.llm_client import llm
            from core.llm_client import llm
            user_input = run_async(llm.transcribe_audio(audio_input.getvalue()))
            # Show the transcribed text in a toast notification so you know what it heard
            st.toast(f"Transcribed: {user_input[:50]}...") 

    # Process the Input
    if user_input:
        st.session_state.interview_state["history"].append({"role": "user", "content": user_input})
        
        if st.session_state.interview_state["turn_count"] >= st.session_state.interview_state["max_turns"]:
            st.session_state.interview_completed = True
        else:
            with st.spinner("Principal Engineer is evaluating your defense..."):
                new_state = run_async(st.session_state.graph.ainvoke(st.session_state.interview_state))
                st.session_state.interview_state.update(new_state)
        st.rerun()











       # python -m streamlit run interfaces/ui_interviewer.py