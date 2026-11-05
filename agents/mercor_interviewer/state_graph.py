# agents/mercor_interviewer/state_graph.py
import logging
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

from core.schemas import EvaluationScore, InterviewTurn
from core.llm_client import llm

logger = logging.getLogger(__name__)

# --- 1. Define the State Schema ---
class InterviewState(TypedDict):
    context: str                  # The generated Architecture.md report
    history: List[dict]           # Standard Chat history [{"role": "user/assistant", "content": "..."}]
    evaluations: List[EvaluationScore] # Ongoing grades
    turn_count: int               # How many questions asked
    max_turns: int                # Usually 3 or 5 for a mock session
    current_question: str         # The active question

# --- 2. The Node Functions ---
async def generate_question_node(state: InterviewState) -> dict:
    """Generates the next adversarial question based on the architecture report and chat history."""
    
    system_prompt = (
        "You are a ruthless Principal Systems Architect at a Tier-1 quant fund conducting a technical screen. "
        "Your objective is to break the candidate's architecture. "
        "Review the candidate's Architecture Report. Pick ONE specific microservice, contract, or database interaction they built. "
        "Ask a highly specific, adversarial question. Force them to defend their choice of concurrency model, latency overhead, or failure recovery. "
        "If they ramble, cut them down in the evaluation. If they give a generic answer, fail them on the technical score and demand quantifiable metrics. "
        "Do not be polite. Be strictly professional, terse, and demanding."
    )
    
    # We serialize history to string for the prompt context
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in state['history']])
    
    user_prompt = (
        f"Architecture Context:\n{state['context']}\n\n"
        f"Interview History:\n{history_str}\n\n"
        "Generate the next InterviewTurn (evaluation of their last answer, and the next question)."
    )

    try:
        # Call our shared core LLM client
        turn: InterviewTurn = await llm.generate_structured(
            system_prompt=system_prompt, 
            user_prompt=user_prompt, 
            response_model=InterviewTurn
        )
        
        # Append new evaluation if it exists (skip on turn 1)
        new_evals = state["evaluations"].copy()
        if turn.evaluation_of_previous_answer:
            new_evals.append(turn.evaluation_of_previous_answer)

        # We append the AI's question to the chat history
        new_history = state["history"].copy()
        new_history.append({"role": "assistant", "content": turn.next_question})

        return {
            "current_question": turn.next_question,
            "evaluations": new_evals,
            "turn_count": state["turn_count"] + 1,
            "history": new_history
        }
    except Exception as e:
        logger.error(f"Failed to generate question: {e}")
        return {"current_question": "Error generating question. Please restart."}

def check_termination(state: InterviewState) -> str:
    """Routing logic: Should we keep interviewing or end?"""
    if state["turn_count"] >= state["max_turns"]:
        return END
    return "generate_question_node"

# --- 3. Build the Graph ---
def build_interview_graph():
    workflow = StateGraph(InterviewState)
    
    # Add our single operational node for this MVP
    workflow.add_node("generate_question_node", generate_question_node)
    
    # Define the flow
    workflow.add_edge(START, "generate_question_node")
    
    # We pause execution after generating a question so the UI can get user input
    # In LangGraph, returning END stops the loop, allowing the external Streamlit UI to append the user message and resume.
    workflow.add_conditional_edges("generate_question_node", check_termination)
    
    # Compile the graph
    return workflow.compile()