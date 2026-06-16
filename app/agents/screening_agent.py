# Import BaseModel to create structured outputs
from pydantic import BaseModel

# Import call_llm to use Groq through LangChain
from app.utils.llm import call_llm

# Import json to parse LLM responses
import json


# Create a structured screening result
class ScreeningResult(BaseModel):

    # Extracted symptoms
    symptoms: list[str]

    # Detected red flags
    red_flags: list[str]

    # Assigned risk level
    risk_level: str

    # Follow-up questions
    follow_up_questions: list[str]

    # Doctor summary
    doctor_summary: str

    # Screening explanation
    explanation: str


# Main screening agent
def run_screening_agent(user_message: str) -> ScreeningResult:

    # System prompt
    system_prompt = """
    You are a Cancer Symptom Screening Agent.

    Your job is NOT to diagnose cancer.

    Your job is to:

    1. Extract symptoms
    2. Detect red flags
    3. Assign risk level:
       LOW
       MEDIUM
       HIGH
       URGENT

    4. Generate follow-up questions
    5. Create a short doctor summary
    6. Explain findings safely

    Return ONLY valid JSON.

    Format:

    {
        "symptoms": [],
        "red_flags": [],
        "risk_level": "",
        "follow_up_questions": [],
        "doctor_summary": "",
        "explanation": ""
    }

    Rules:

    - Never diagnose.
    - Never recommend treatment.
    - Never claim the patient has cancer.
    - Use simple English.
    """

    # User prompt
    user_prompt = f"""
    User message:

    {user_message}
    """

    # Call LLM
    raw_response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    try:

        # Parse JSON
        parsed = json.loads(raw_response)

        return ScreeningResult(
            symptoms=parsed.get("symptoms", []),
            red_flags=parsed.get("red_flags", []),
            risk_level=parsed.get("risk_level", "MEDIUM"),
            follow_up_questions=parsed.get(
                "follow_up_questions",
                [],
            ),
            doctor_summary=parsed.get(
                "doctor_summary",
                "",
            ),
            explanation=parsed.get(
                "explanation",
                "",
            ),
        )

    except Exception:

        # Safe fallback
        return ScreeningResult(
            symptoms=[],
            red_flags=[],
            risk_level="MEDIUM",
            follow_up_questions=[
                "Could you tell me more about your symptoms?"
            ],
            doctor_summary="Screening agent fallback response.",
            explanation=(
                "I could not fully analyze the symptoms. "
                "Please consult a healthcare professional."
            ),
        )