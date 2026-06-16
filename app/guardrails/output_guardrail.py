# Import BaseModel to create a structured output guardrail result
from pydantic import BaseModel


# Create a result model for the output guardrail
class OutputGuardrailResult(BaseModel):

    # Store whether the answer is approved
    approved: bool

    # Store the reason for approval or correction
    reason: str

    # Store the final safe answer
    final_answer: str


# List unsafe phrases that should not appear in medical AI answers
UNSAFE_OUTPUT_PHRASES = [
    "you have cancer",
    "you definitely have cancer",
    "you do not need to see a doctor",
    "do not see a doctor",
    "stop your medicine",
    "stop taking your medicine",
    "this will cure you",
    "guaranteed cure",
    "you are eligible for this trial",
]


# Create the output guardrail function
def run_output_guardrail(answer: str) -> OutputGuardrailResult:

    # Convert answer to lowercase for safety checking
    lower_answer = answer.lower()

    # Check each unsafe phrase
    for phrase in UNSAFE_OUTPUT_PHRASES:

        # If unsafe phrase exists in the answer
        if phrase in lower_answer:

            # Return a corrected safe answer
            return OutputGuardrailResult(
                approved=False,
                reason=f"Unsafe phrase detected: {phrase}",
                final_answer=(
                    "I cannot provide a final diagnosis, treatment decision, or guaranteed medical outcome. "
                    "Cancer-related symptoms and reports must be reviewed by a qualified healthcare professional. "
                    "Please speak with a doctor or oncologist for personal medical advice."
                ),
            )

    # Check whether the answer includes a doctor or healthcare safety note
    has_doctor_note = "doctor" in lower_answer or "healthcare professional" in lower_answer

    # If doctor safety note is missing
    if not has_doctor_note:

        # Add a safety note to the answer
        safe_answer = (
            answer
            + "\n\nSafety note: This information is for education only and does not replace advice from a doctor or qualified healthcare professional."
        )

        # Return approved answer with safety note added
        return OutputGuardrailResult(
            approved=True,
            reason="Doctor safety note was missing, so it was added.",
            final_answer=safe_answer,
        )

    # Return approved answer without changes
    return OutputGuardrailResult(
        approved=True,
        reason="Output passed safety checks.",
        final_answer=answer,
    )