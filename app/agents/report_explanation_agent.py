# Import BaseModel to create a structured report explanation result
from pydantic import BaseModel

# Import call_llm to call Groq through LangChain
from app.utils.llm import call_llm

# Import medical entity extraction tool to extract medical terms
from app.tools.entity_extraction_tool import medical_entity_extraction_tool


# Create structured result for report explanation
class ReportExplanationResult(BaseModel):

    # Store the final report explanation answer
    answer: str

    # Store extracted medical entities or terms
    extracted_entities: str

    # Store safety level of the explanation
    safety_level: str


# Create the report explanation agent function
def run_report_explanation_agent(user_message: str) -> ReportExplanationResult:

    # Extract medical entities from the report text or user message
    extracted_entities = medical_entity_extraction_tool.invoke(
        {
            "text": user_message
        }
    )

    # Create system prompt for report explanation
    system_prompt = """
    You are a Medical Report Explanation Agent for a cancer-related AI assistant.

    Your job:
    - Explain medical report text in simple English.
    - Explain terms such as biopsy, pathology, CT, MRI, staging, grade, biomarkers, benign, malignant, suspicious, lesion, mass, metastasis.
    - Identify what information should be discussed with a doctor.
    - Generate useful questions the user can ask their doctor.

    Safety rules:
    - Do NOT give a final diagnosis.
    - Do NOT say the patient definitely has cancer.
    - Do NOT recommend treatment.
    - Do NOT interpret imaging or pathology as a doctor.
    - Do NOT replace a doctor, pathologist, radiologist, or oncologist.
    - Always say the report must be confirmed by a qualified healthcare professional.

    Output format:
    1. Simple explanation
    2. Important terms found
    3. Possible questions to ask the doctor
    4. Safety note
    """

    # Create user prompt with user message and extracted entities
    user_prompt = f"""
    User message or report text:
    {user_message}

    Extracted medical entities:
    {extracted_entities}

    Explain this safely in simple English.
    """

    # Generate safe explanation using LLM
    answer = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
    )

    # Return structured result
    return ReportExplanationResult(
        answer=answer,
        extracted_entities=extracted_entities,
        safety_level="medical_report_explanation_requires_doctor_confirmation",
    )