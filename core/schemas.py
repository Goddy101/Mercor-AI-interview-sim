# core/schemas.py
from pydantic import BaseModel, Field

# --- CODEBASE ARCHITECT SCHEMAS ---

class Vulnerability(BaseModel):
    file_path: str = Field(..., description="The exact file path containing the issue.")
    issue_type: str = Field(..., description="Type of issue: e.g., 'N+1 Query', 'Race Condition', 'Synchronous Blocking'.")
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    recommendation: str = Field(..., description="Specific architectural fix required.")

class ArchitectureReport(BaseModel):
    system_overview: str = Field(..., description="Executive summary of the system architecture.")
    concurrency_model: str = Field(..., description="Analysis of how the system handles concurrent loads and state.")
    data_flow: str = Field(..., description="Mapping of how data moves from DB to API to Client.")
    vulnerabilities: list[Vulnerability] = Field(default_factory=list, description="List of critical structural flaws.")

# --- MERCOR INTERVIEWER SCHEMAS ---

class EvaluationScore(BaseModel):
    system_architecture_score: int = Field(..., ge=1, le=10, description="Score 1-10 on distributed systems design and state management.")
    latency_and_scale_score: int = Field(..., ge=1, le=10, description="Score 1-10 on understanding Big-O, concurrency, and bottlenecks.")
    conciseness_score: int = Field(..., ge=1, le=10, description="Score 1-10 on directness. Penalize rambling heavily.")
    red_flags: list[str] = Field(default_factory=list, description="Fatal flaws detected (e.g., 'Candidate ignored database locks').")
    missed_tradeoffs: list[str] = Field(default_factory=list, description="Specific trade-offs (e.g., 'CP vs AP', 'Memory vs Speed') they failed to mention.")
    harsh_feedback: str = Field(..., description="Savage, actionable feedback. Write like a strict Staff Engineer who is short on time.")
    
class InterviewTurn(BaseModel):
    evaluation_of_previous_answer: EvaluationScore | None = Field(None, description="Grading of the candidate's last response.")
    next_question: str = Field(..., description="The next adversarial, highly technical follow-up question.")
    expected_key_concepts: list[str] = Field(..., description="What the interviewer expects to hear in a passing answer.")