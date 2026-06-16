# Import tool decorator
from langchain_core.tools import tool


# Create citation checker tool
@tool
def citation_checker_tool(answer: str) -> str:
    """
    Check whether an answer contains sources and a healthcare safety note.
    """

    # Convert answer to lowercase
    lower_answer = answer.lower()

    # Check whether answer contains sources
    has_sources = "sources used:" in lower_answer or "source" in lower_answer

    # Check whether answer mentions doctor safety
    has_safety_note = "doctor" in lower_answer or "healthcare professional" in lower_answer

    # If both are present
    if has_sources and has_safety_note:
        return "Citation check passed. Answer contains sources and safety note."

    # Create issue list
    issues = []

    # If sources missing
    if not has_sources:
        issues.append("Missing sources.")

    # If safety note missing
    if not has_safety_note:
        issues.append("Missing doctor/healthcare safety note.")

    # Return issues
    return "Citation check failed: " + " ".join(issues)