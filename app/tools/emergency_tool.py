# Import tool decorator
from langchain_core.tools import tool


# Define emergency terms
EMERGENCY_TERMS = [
    "vomiting blood",
    "coughing blood",
    "cannot breathe",
    "difficulty breathing",
    "severe chest pain",
    "heavy bleeding",
    "unconscious",
    "seizure",
]


# Create emergency red flag tool
@tool
def emergency_red_flag_tool(text: str) -> str:
    """
    Detect emergency red-flag symptoms from user text.
    """

    # Convert text to lowercase
    lower_text = text.lower()

    # Create detected list
    detected = []

    # Loop through emergency terms
    for term in EMERGENCY_TERMS:

        # Check if term is found
        if term in lower_text:
            detected.append(term)

    # If emergency terms detected
    if detected:
        return (
            f"Emergency red flags detected: {', '.join(detected)}\n"
            "This may be a medical emergency. Please seek urgent medical care now."
        )

    # Return no emergency message
    return "No emergency red flags detected."