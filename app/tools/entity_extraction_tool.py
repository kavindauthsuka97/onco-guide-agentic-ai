# Import json to parse LLM response
import json

# Import tool decorator for LangChain
from langchain_core.tools import tool

# Import call_llm helper
from app.utils.llm import call_llm


# Create medical entity extraction tool
@tool
def medical_entity_extraction_tool(text: str) -> str:
    """
    Extract cancer-related medical entities from user text.
    """

    # Create system prompt
    system_prompt = """
    You are a medical entity extraction tool for a cancer AI system.

    Extract:
    - symptoms
    - cancer_type
    - body_part
    - biomarkers
    - stage
    - treatment_terms
    - report_terms

    Return ONLY valid JSON.
    """

    # Create user prompt
    user_prompt = f"Text: {text}"

    # Call LLM
    raw_response = call_llm(system_prompt, user_prompt, temperature=0.0)

    # Try JSON validation
    try:
        parsed = json.loads(raw_response)
        return json.dumps(parsed, indent=2)

    # If parsing fails
    except Exception:
        return json.dumps(
            {
                "symptoms": [],
                "cancer_type": "",
                "body_part": "",
                "biomarkers": [],
                "stage": "",
                "treatment_terms": [],
                "report_terms": [],
                "error": "Could not parse entity extraction output.",
            },
            indent=2,
        )