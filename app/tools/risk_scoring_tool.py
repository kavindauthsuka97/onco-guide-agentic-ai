# Import tool decorator
from langchain_core.tools import tool


# Create cancer risk scoring tool
@tool
def risk_scoring_tool(symptoms_text: str) -> str:
    """
    Score cancer-related symptoms using simple red-flag rules.
    """

    # Convert text to lowercase
    text = symptoms_text.lower()

    # Create score variable
    score = 0

    # Create empty red flag list
    red_flags = []

    # Define red flag symptoms
    red_flag_terms = [
        "blood in stool",
        "coughing blood",
        "vomiting blood",
        "unexplained weight loss",
        "breast lump",
        "lump",
        "nipple discharge",
        "skin dimpling",
        "persistent cough",
        "difficulty swallowing",
        "severe pain",
    ]

    # Loop through red flag terms
    for term in red_flag_terms:

        # If term is found
        if term in text:
            score += 2
            red_flags.append(term)

    # Assign risk level
    if score >= 6:
        risk_level = "HIGH"
    elif score >= 3:
        risk_level = "MEDIUM"
    elif score > 0:
        risk_level = "LOW"
    else:
        risk_level = "UNKNOWN"

    # Return formatted result
    return (
        f"Risk level: {risk_level}\n"
        f"Score: {score}\n"
        f"Red flags detected: {', '.join(red_flags) if red_flags else 'None'}\n"
        f"Safety note: This is not a diagnosis. A healthcare professional should evaluate concerning symptoms."
    )