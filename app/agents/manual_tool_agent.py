# Import BaseModel to create structured output
from pydantic import BaseModel

# Import medical entity extraction tool
from app.tools.entity_extraction_tool import medical_entity_extraction_tool

# Import risk scoring tool
from app.tools.risk_scoring_tool import risk_scoring_tool

# Import citation checker tool
from app.tools.citation_checker_tool import citation_checker_tool

# Import emergency red flag tool
from app.tools.emergency_tool import emergency_red_flag_tool

# Import BM25 keyword search tool
from app.tools.bm25_search_tool import bm25_search_tool

# Import call_llm to summarize tool outputs safely
from app.utils.llm import call_llm

# Import real MCP PubMed caller
from app.mcp_servers.mcp_tool_adapter import call_pubmed_mcp

# Import real MCP ClinicalTrials caller
from app.mcp_servers.mcp_tool_adapter import call_clinical_trials_mcp

# Import real MCP Vector DB caller
from app.mcp_servers.mcp_tool_adapter import call_vector_db_mcp


# Create structured output model
class ManualToolAgentResult(BaseModel):

    # Store final answer
    answer: str

    # Store selected tool name
    selected_tool: str

    # Store tool selection reason
    tool_reason: str

    # Store raw tool output
    tool_output: str


# Select a tool using fixed deterministic rules
def select_tool(user_message: str) -> tuple[str, str]:

    # Convert message to lowercase
    text = user_message.lower()

    # Emergency route
    if (
        "vomiting blood" in text
        or "coughing blood" in text
        or "cannot breathe" in text
        or "severe chest pain" in text
    ):
        return "emergency_red_flag_tool", "Emergency red-flag wording detected."

    # PubMed MCP route
    if (
        "pubmed" in text
        or "research paper" in text
        or "recent paper" in text
        or "papers" in text
    ):
        return "pubmed_mcp", "Research paper request detected. Using real MCP server."

    # ClinicalTrials MCP route
    if "clinical trial" in text or "trial" in text:
        return "clinical_trials_mcp", "Clinical trial request detected. Using real MCP server."

    # BM25 local route
    if "keyword search" in text or "bm25" in text:
        return "bm25_search_tool", "Keyword/BM25 search request detected."

    # Risk scoring local route
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
        return "risk_scoring_tool", "Symptom-related request detected."

    # Entity extraction local route
    if (
        "extract" in text
        or "entities" in text
        or "biomarker" in text
        or "mutation" in text
    ):
        return "medical_entity_extraction_tool", "Entity extraction or biomarker request detected."

    # Citation checker local route
    if "citation" in text or "source check" in text or "verify answer" in text:
        return "citation_checker_tool", "Citation checking request detected."

    # Default vector DB MCP route
    return "vector_db_mcp", "Default safe retrieval route selected. Using real MCP server."


# Execute the selected tool safely
def execute_selected_tool(tool_name: str, user_message: str) -> str:

    # Use local emergency tool
    if tool_name == "emergency_red_flag_tool":
        return emergency_red_flag_tool.invoke(
            {
                "text": user_message,
            }
        )

    # Use PubMed through MCP server
    if tool_name == "pubmed_mcp":
        return call_pubmed_mcp(
            query=user_message,
            max_results=5,
        )

    # Use ClinicalTrials through MCP server
    if tool_name == "clinical_trials_mcp":
        return call_clinical_trials_mcp(
            condition=user_message,
            location="",
            max_results=5,
        )

    # Use local BM25 tool
    if tool_name == "bm25_search_tool":
        return bm25_search_tool.invoke(
            {
                "query": user_message,
                "top_k": 4,
            }
        )

    # Use local risk scoring tool
    if tool_name == "risk_scoring_tool":
        return risk_scoring_tool.invoke(
            {
                "symptoms_text": user_message,
            }
        )

    # Use local entity extraction tool
    if tool_name == "medical_entity_extraction_tool":
        return medical_entity_extraction_tool.invoke(
            {
                "text": user_message,
            }
        )

    # Use local citation checker tool
    if tool_name == "citation_checker_tool":
        return citation_checker_tool.invoke(
            {
                "answer": user_message,
            }
        )

    # Default: use vector DB through MCP server
    return call_vector_db_mcp(
        query=user_message,
        top_k=4,
    )


# Main Manual Tool-Calling Agent
def run_manual_tool_agent(user_message: str) -> ManualToolAgentResult:

    # Select tool using rules
    selected_tool, tool_reason = select_tool(user_message)

    # Execute selected tool
    tool_output = execute_selected_tool(selected_tool, user_message)

    # Create safe summarization system prompt
    system_prompt = """
    You are a safe Manual Tool-Calling Agent for a cancer-related medical AI system.

    Your job:
    - Explain the tool result in simple English.
    - Do not diagnose cancer.
    - Do not give treatment decisions.
    - Do not give medication dosage.
    - If clinical trials are shown, say eligibility must be confirmed by the trial team.
    - If symptoms are mentioned, recommend speaking with a healthcare professional.
    - Use only the tool output provided.
    """

    # Create user prompt
    user_prompt = f"""
    User message:
    {user_message}

    Selected tool:
    {selected_tool}

    Tool selection reason:
    {tool_reason}

    Tool output:
    {tool_output}

    Summarize safely.
    """

    # Generate safe answer
    answer = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
    )

    # Return structured result
    return ManualToolAgentResult(
        answer=answer,
        selected_tool=selected_tool,
        tool_reason=tool_reason,
        tool_output=tool_output,
    )