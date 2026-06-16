# Import json to parse the LLM response as JSON
import json

# Import re to detect PII patterns using regular expressions
import re

# Import BaseModel to create structured guardrail results
from pydantic import BaseModel

# Import call_llm to use Groq through LangChain
from app.utils.llm import call_llm


# Create the structured result returned by the guardrail
class UnifiedGuardrailResult(BaseModel):

    # Store whether the message is allowed to continue
    allowed: bool

    # Store the risk level: low, medium, high, or red
    risk_level: str

    # Store the reason for the decision
    reason: str

    # Store the sanitized user message after PII masking
    sanitized_message: str

    # Store the recommended route for the supervisor later
    route_hint: str

    # Store safety message if the input is blocked
    safety_message: str | None = None


# Define emergency keywords for fast safety detection
EMERGENCY_KEYWORDS = [
    "vomiting blood",
    "coughing blood",
    "cannot breathe",
    "difficulty breathing",
    "severe chest pain",
    "heavy bleeding",
    "unconscious",
    "seizure",
]


# Define unsafe medical request keywords
UNSAFE_MEDICAL_KEYWORDS = [
    "give me chemotherapy dose",
    "what dose should i take",
    "can i stop my medicine",
    "should i stop my medicine",
    "should i avoid doctor",
    "do i need doctor",
]


# Define regex patterns to detect simple PII
PII_PATTERNS = {
    # Detect email addresses
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",

    # Detect phone numbers with 10 or more digits
    "PHONE": r"(\+?\d[\d\s\-]{8,}\d)",

    # Detect Sri Lankan NIC old format or new format
    "NIC": r"\b(\d{9}[vVxX]|\d{12})\b",
}


# Create a function to mask PII from the user message
def mask_pii(text: str) -> tuple[str, list[str]]:

    # Store the sanitized text
    sanitized_text = text

    # Store detected PII types
    detected_pii = []

    # Loop through each PII pattern
    for pii_type, pattern in PII_PATTERNS.items():

        # Check if the pattern exists in the text
        if re.search(pattern, sanitized_text):

            # Add detected PII type to the list
            detected_pii.append(pii_type)

            # Replace detected PII with a safe placeholder
            sanitized_text = re.sub(pattern, f"[{pii_type}_MASKED]", sanitized_text)

    # Return sanitized text and detected PII list
    return sanitized_text, detected_pii


# Create a function for fast keyword-based safety check
def keyword_safety_check(text: str) -> UnifiedGuardrailResult | None:

    # Convert text to lowercase for easier matching
    lower_text = text.lower()

    # Check emergency keywords
    for keyword in EMERGENCY_KEYWORDS:

        # If emergency keyword is found, block normal flow
        if keyword in lower_text:

            # Return a red-risk blocked result
            return UnifiedGuardrailResult(
                allowed=False,
                risk_level="red",
                reason=f"Emergency keyword detected: {keyword}",
                sanitized_message=text,
                route_hint="emergency",
                safety_message=(
                    "This may be a medical emergency. "
                    "Please seek urgent medical care now or contact your local emergency service."
                ),
            )

    # Check unsafe medical request keywords
    for keyword in UNSAFE_MEDICAL_KEYWORDS:

        # If unsafe keyword is found, block normal flow
        if keyword in lower_text:

            # Return a high-risk blocked result
            return UnifiedGuardrailResult(
                allowed=False,
                risk_level="high",
                reason=f"Unsafe medical request detected: {keyword}",
                sanitized_message=text,
                route_hint="blocked_medical_advice",
                safety_message=(
                    "I cannot provide direct treatment, medication, or chemotherapy decisions. "
                    "Please discuss this with a qualified doctor or oncologist."
                ),
            )

    # Return None if no keyword risk is found
    return None


# Create a function to classify semantic risk using the LLM
def semantic_safety_check(text: str) -> dict:

    # Create the system instruction for the LLM guardrail
    system_prompt = """
    You are a medical AI input safety classifier.

    Classify the user's message for a cancer-related AI assistant.

    Return ONLY valid JSON with these keys:
    allowed: true or false
    risk_level: "low", "medium", "high", or "red"
    route_hint: "general_chat", "screening", "rag", "clinical_trial", "report_explanation", "emergency", or "blocked_medical_advice"
    reason: short reason
    safety_message: short safety message if blocked, otherwise empty string

    Rules:
    - Red risk means possible emergency.
    - High risk means unsafe medical decision request, such as diagnosis, medication dose, treatment decision, or stopping medicine.
    - Medium risk means symptom screening or report explanation that is allowed but needs caution.
    - Low risk means general education.
    - Do not diagnose.
    - Do not give treatment decisions.
    """

    # Create the user prompt for the LLM guardrail
    user_prompt = f"""
    User message:
    {text}

    Classify this message as JSON.
    """

    # Call the LLM using our LangChain Groq helper
    raw_response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    # Try to parse the LLM response as JSON
    try:

        # Convert JSON text into a Python dictionary
        parsed = json.loads(raw_response)

        # Return the parsed dictionary
        return parsed

    # If parsing fails, use a safe fallback
    except Exception:

        # Return fallback classification
        return {
            "allowed": True,
            "risk_level": "medium",
            "route_hint": "general_chat",
            "reason": "LLM guardrail JSON parsing failed, so safe fallback was used.",
            "safety_message": "",
        }


# Create the main unified input guardrail function
def run_unified_input_guardrail(user_message: str) -> UnifiedGuardrailResult:

    # Mask PII before sending text to the LLM
    sanitized_message, detected_pii = mask_pii(user_message)

    # Run fast keyword safety check first
    keyword_result = keyword_safety_check(sanitized_message)

    # If keyword check blocks the message
    if keyword_result is not None:

        # Add PII information to the reason if PII was found
        if detected_pii:

            # Update reason with detected PII types
            keyword_result.reason += f" | PII masked: {detected_pii}"

        # Return the blocked keyword result
        return keyword_result

    # Run LLM-based semantic safety check
    semantic_result = semantic_safety_check(sanitized_message)

    # Read allowed value from semantic result
    allowed = bool(semantic_result.get("allowed", True))

    # Read risk level from semantic result
    risk_level = semantic_result.get("risk_level", "medium")

    # Read route hint from semantic result
    route_hint = semantic_result.get("route_hint", "general_chat")

    # Read reason from semantic result
    reason = semantic_result.get("reason", "Semantic guardrail completed.")

    # Read safety message from semantic result
    safety_message = semantic_result.get("safety_message", "")

    # Add PII masking information to the reason if needed
    if detected_pii:

        # Add detected PII types to reason
        reason += f" | PII masked: {detected_pii}"

    # If semantic guardrail blocks the message
    if not allowed:

        # Return blocked result
        return UnifiedGuardrailResult(
            allowed=False,
            risk_level=risk_level,
            reason=reason,
            sanitized_message=sanitized_message,
            route_hint=route_hint,
            safety_message=safety_message or (
                "I cannot safely answer this request. "
                "Please speak with a qualified healthcare professional."
            ),
        )

    # Return allowed result
    return UnifiedGuardrailResult(
        allowed=True,
        risk_level=risk_level,
        reason=reason,
        sanitized_message=sanitized_message,
        route_hint=route_hint,
        safety_message=None,
    )