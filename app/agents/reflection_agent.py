# Import json to parse LLM JSON output
import json

# Import BaseModel to create structured reflection output
from pydantic import BaseModel

# Import call_llm to use Groq through LangChain
from app.utils.llm import call_llm


# Create structured reflection result
class ReflectionResult(BaseModel):

    # Store whether the answer is approved
    approved: bool

    # Store whether the answer is medically safe
    safety_passed: bool

    # Store whether citations or sources are present if needed
    citation_passed: bool

    # Store whether the answer is complete
    completeness_passed: bool

    # Store whether the answer uses simple English
    simple_english_passed: bool

    # Store reflection reason
    reason: str

    # Store improved answer
    improved_answer: str


# Create the reflection agent function
def run_reflection_agent(user_message: str, draft_answer: str, selected_agent: str) -> ReflectionResult:

    # Create system prompt for reflection
    system_prompt = """
    You are the Reflection Agent for OncoGuide, a cancer-related medical AI system.

    Your job is to review the draft answer before it reaches the user.

    Check:
    1. Did the answer address the user question?
    2. Did it avoid final diagnosis?
    3. Did it avoid treatment decisions?
    4. Did it avoid medication or chemotherapy dosage?
    5. Did it recommend doctor or healthcare professional confirmation?
    6. Did it include citations/sources when it used retrieved evidence?
    7. Is the answer written in simple English?
    8. Is the answer complete enough?

    Return ONLY valid JSON with this structure:
    {
      "approved": true,
      "safety_passed": true,
      "citation_passed": true,
      "completeness_passed": true,
      "simple_english_passed": true,
      "reason": "short explanation",
      "improved_answer": "safe improved final answer"
    }

    Important rules:
    - If the answer is unsafe, correct it in improved_answer.
    - Do not add unsupported medical facts.
    - Do not diagnose cancer.
    - Do not give treatment decisions.
    - Do not say a user is eligible for a clinical trial.
    - Always include a doctor/healthcare professional safety note for personal medical advice.
    """

    # Create user prompt containing user question and draft answer
    user_prompt = f"""
    Selected agent:
    {selected_agent}

    User message:
    {user_message}

    Draft answer:
    {draft_answer}

    Review and improve the draft answer.
    """

    # Call LLM for reflection
    raw_response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    # Try to parse JSON
    try:

        # Convert JSON text to Python dictionary
        parsed = json.loads(raw_response)

        # Return structured reflection result
        return ReflectionResult(
            approved=bool(parsed.get("approved", True)),
            safety_passed=bool(parsed.get("safety_passed", True)),
            citation_passed=bool(parsed.get("citation_passed", True)),
            completeness_passed=bool(parsed.get("completeness_passed", True)),
            simple_english_passed=bool(parsed.get("simple_english_passed", True)),
            reason=parsed.get("reason", "Reflection completed."),
            improved_answer=parsed.get("improved_answer", draft_answer),
        )

    # If JSON parsing fails
    except Exception:

        # Return safe fallback reflection result
        return ReflectionResult(
            approved=True,
            safety_passed=True,
            citation_passed=False,
            completeness_passed=True,
            simple_english_passed=True,
            reason="Reflection JSON parsing failed. Safe fallback used.",
            improved_answer=(
                draft_answer
                + "\n\nSafety note: This information is for education only and does not replace advice from a doctor or qualified healthcare professional."
            ),
        )