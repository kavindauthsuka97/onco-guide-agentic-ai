# Import json to parse LLM JSON output
import json

# Import BaseModel to create a structured supervisor result
from pydantic import BaseModel

# Import call_llm to use Groq through LangChain
from app.utils.llm import call_llm


# Create a structured result for the supervisor decision
class SupervisorResult(BaseModel):

    # Store the selected agent name
    selected_agent: str

    # Store the confidence level
    confidence: str

    # Store the reason for selecting that agent
    reason: str


# Create the supervisor agent function
def run_supervisor_agent(user_message: str, route_hint: str = "general_chat") -> SupervisorResult:

    # Create the system prompt for the supervisor
    system_prompt = """
    You are the Supervisor Agent for a cancer-related medical AI system.

    Available agents:
    - screening_agent: symptoms, red flags, risk screening
    - rag_agent: general cancer education from trusted documents
    - clinical_trial_agent: clinical trial search
    - report_explanation_agent: biopsy, lab, CT, MRI, pathology, report explanation
    - react_agent: complex multi-tool requests needing flexible tool use
    - manual_tool_agent: predictable tool requests where deterministic safety is better
    - general_chat_agent: greetings or simple conversation

    Return ONLY valid JSON:
    {
      "selected_agent": "...",
      "confidence": "low/medium/high",
      "reason": "..."
    }

    Rules:
    - If user asks to use a specific tool such as PubMed, BM25, vector search, NCI PDQ, citation checker, risk scoring, route to manual_tool_agent.
    - If user asks papers AND trials together, route to react_agent.
    - If user asks recent papers plus clinical trials, route to react_agent.
    - If user asks only clinical trials, route to clinical_trial_agent.
    - If user asks symptoms, route to screening_agent.
    - If user asks report explanation, route to report_explanation_agent.
    - If user asks general cancer education, route to rag_agent.
    - If user says hello, route to general_chat_agent.
    """

    # Create user prompt
    user_prompt = f"""
    Route hint:
    {route_hint}

    User message:
    {user_message}

    Select best agent.
    """

    # Call LLM supervisor
    raw_response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    # Try parsing JSON
    try:

        # Convert JSON string into dictionary
        parsed = json.loads(raw_response)

        # Return supervisor result
        return SupervisorResult(
            selected_agent=parsed.get("selected_agent", "rag_agent"),
            confidence=parsed.get("confidence", "medium"),
            reason=parsed.get("reason", "Supervisor selected default route."),
        )

    # If LLM JSON parsing fails
    except Exception:

        # Use fallback router
        return fallback_supervisor_router(user_message, route_hint)


# Create fallback supervisor router
def fallback_supervisor_router(user_message: str, route_hint: str = "general_chat") -> SupervisorResult:

    # Convert message to lowercase
    text = user_message.lower()

    # Route explicit tool-use requests to manual tool agent
    if (
        "use pubmed" in text
        or "pubmed" in text
        or "bm25" in text
        or "keyword search" in text
        or "vector search" in text
        or "nci pdq" in text
        or "pdq" in text
        or "citation checker" in text
        or "check citation" in text
        or "risk score" in text
        or "use tool" in text
    ):

        # Return manual tool agent
        return SupervisorResult(
            selected_agent="manual_tool_agent",
            confidence="high",
            reason="Explicit deterministic tool request detected.",
        )

    # Route complex multi-tool research questions to ReAct
    if (
        ("paper" in text and "trial" in text)
        or ("pubmed" in text and "clinical" in text)
        or ("research" in text and "trial" in text)
        or ("recent papers" in text and "trials" in text)
    ):

        # Return ReAct route
        return SupervisorResult(
            selected_agent="react_agent",
            confidence="high",
            reason="Complex multi-tool research request detected.",
        )

    # Route clinical trial questions
    if "trial" in text or "clinical trial" in text:

        # Return clinical trial route
        return SupervisorResult(
            selected_agent="clinical_trial_agent",
            confidence="high",
            reason="Clinical trial keyword detected.",
        )

    # Route report explanation questions
    if (
        "report" in text
        or "biopsy" in text
        or "pathology" in text
        or "ct scan" in text
        or "mri" in text
        or "lab result" in text
    ):

        # Return report explanation route
        return SupervisorResult(
            selected_agent="report_explanation_agent",
            confidence="high",
            reason="Medical report keyword detected.",
        )

    # Route symptom screening questions
    if (
        "lump" in text
        or "blood" in text
        or "pain" in text
        or "weight loss" in text
        or "cough" in text
        or "fatigue" in text
        or "stool" in text
        or "swelling" in text
    ):

        # Return screening route
        return SupervisorResult(
            selected_agent="screening_agent",
            confidence="high",
            reason="Symptom keyword detected.",
        )

    # Route greeting
    if text in ["hi", "hello", "hey"]:

        # Return general chat
        return SupervisorResult(
            selected_agent="general_chat_agent",
            confidence="high",
            reason="Greeting detected.",
        )

    # Default RAG
    return SupervisorResult(
        selected_agent="rag_agent",
        confidence="medium",
        reason="Default route for general cancer education.",
    )