# Import BaseModel to create structured clinical trial result
from pydantic import BaseModel

# Import clinical trial search tool from tools layer
from app.tools.clinical_trials_tool import clinical_trials_search_tool

# Import medical entity extraction tool
from app.tools.entity_extraction_tool import medical_entity_extraction_tool

# Import call_llm to summarize results safely
from app.utils.llm import call_llm


# Create structured result model
class ClinicalTrialResult(BaseModel):

    # Store final answer
    answer: str

    # Store condition used for search
    condition: str

    # Store location used for search
    location: str


# Create clinical trial matching agent
def run_clinical_trial_agent(user_message: str) -> ClinicalTrialResult:

    # Extract medical entities from user message
    extracted_entities = medical_entity_extraction_tool.invoke(
        {
            "text": user_message
        }
    )

    # Create system prompt to identify condition and location
    system_prompt = """
    You are a clinical trial search assistant.

    Extract:
    1. cancer condition
    2. location if mentioned

    Return simple text only in this format:
    condition: ...
    location: ...

    If location is missing, use empty location.
    """

    # Create user prompt
    user_prompt = f"""
    User message:
    {user_message}

    Extracted entities:
    {extracted_entities}
    """

    # Ask LLM to extract search condition and location
    extraction_result = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    # Set default condition
    condition = "cancer"

    # Set default location
    location = ""

    # Loop through each line in extraction result
    for line in extraction_result.splitlines():

        # Check condition line
        if line.lower().startswith("condition:"):

            # Extract condition value
            condition = line.split(":", 1)[1].strip()

        # Check location line
        if line.lower().startswith("location:"):

            # Extract location value
            location = line.split(":", 1)[1].strip()

    # If condition is empty
    if not condition:

        # Use generic cancer condition
        condition = "cancer"

    # Search ClinicalTrials.gov using the tool
    trial_results = clinical_trials_search_tool.invoke(
        {
            "condition": condition,
            "location": location,
            "max_results": 5,
        }
    )

    # Create summarization system prompt
    summary_system_prompt = """
    You are a safe clinical trial matching assistant.

    Rules:
    - Do not say the user is eligible.
    - Say these are possible trial results only.
    - Eligibility must be confirmed by the trial team or doctor.
    - Use simple English.
    - Do not recommend joining a trial as medical advice.
    """

    # Create summarization user prompt
    summary_user_prompt = f"""
    User message:
    {user_message}

    Clinical trial search condition:
    {condition}

    Clinical trial search location:
    {location}

    Trial search results:
    {trial_results}

    Summarize the results safely.
    """

    # Generate safe final answer
    final_answer = call_llm(
        system_prompt=summary_system_prompt,
        user_prompt=summary_user_prompt,
        temperature=0.1,
    )

    # Return structured result
    return ClinicalTrialResult(
        answer=final_answer,
        condition=condition,
        location=location,
    )