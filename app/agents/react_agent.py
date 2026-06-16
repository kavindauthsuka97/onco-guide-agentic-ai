# Import BaseModel to create a structured ReAct result
from pydantic import BaseModel

# Import SystemMessage to give the agent system instructions
from langchain_core.messages import SystemMessage

# Import HumanMessage to send the user request
from langchain_core.messages import HumanMessage

# Import ToolMessage to send tool results back to the LLM
from langchain_core.messages import ToolMessage

# Import get_llm to create the Groq LangChain model
from app.utils.llm import get_llm

# Import all tools from the tool registry
from app.tools.tool_registry import ALL_TOOLS


# Create structured output for the ReAct agent
class ReActAgentResult(BaseModel):

    # Store final answer text
    answer: str

    # Store names of tools used
    tools_used: list[str]

    # Store number of tool steps used
    tool_steps: int


# Create the main ReAct agent function
def run_react_agent(user_message: str) -> ReActAgentResult:

    # Create the Groq LLM
    llm = get_llm(temperature=0.1)

    # Bind tools to the LLM so the model can call them
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # Create a dictionary to find tools by tool name
    tool_map = {tool.name: tool for tool in ALL_TOOLS}

    # Create system instructions for the ReAct agent
    system_message = SystemMessage(
        content=(
            "You are the ReAct Agent for OncoGuide, a cancer-related medical AI system.\n\n"
            "Your job is to reason about the user request and call useful tools when needed.\n\n"
            "Available tool abilities include:\n"
            "- PubMed search\n"
            "- ClinicalTrials.gov search\n"
            "- NCI PDQ/local document search\n"
            "- Medical entity extraction\n"
            "- Risk scoring\n"
            "- Report parsing\n"
            "- Citation checking\n"
            "- Emergency red-flag checking\n"
            "- Vector search\n"
            "- BM25 keyword search\n\n"
            "Safety rules:\n"
            "- Do not diagnose cancer.\n"
            "- Do not give treatment decisions.\n"
            "- Do not give medication or chemotherapy dosage.\n"
            "- Do not say the user is eligible for a clinical trial.\n"
            "- For clinical trials, say eligibility must be confirmed by the trial team.\n"
            "- Use simple English.\n"
            "- Include sources or tool evidence when available.\n"
            "- Recommend speaking with a qualified healthcare professional for personal medical advice."
        )
    )

    # Create the first human message
    human_message = HumanMessage(content=user_message)

    # Store all messages in conversation history
    messages = [system_message, human_message]

    # Store tool names used
    tools_used = []

    # Set maximum number of tool-calling loops to control latency
    max_steps = 5

    # Start tool-calling loop
    for step in range(max_steps):

        # Ask the LLM what to do next
        ai_message = llm_with_tools.invoke(messages)

        # Add the AI message to conversation history
        messages.append(ai_message)

        # Get tool calls from AI message
        tool_calls = getattr(ai_message, "tool_calls", [])

        # If there are no tool calls, this is the final answer
        if not tool_calls:

            # Return final answer
            return ReActAgentResult(
                answer=ai_message.content,
                tools_used=tools_used,
                tool_steps=len(tools_used),
            )

        # Loop through each tool call
        for tool_call in tool_calls:

            # Get tool name
            tool_name = tool_call["name"]

            # Get tool arguments
            tool_args = tool_call["args"]

            # Get tool call ID
            tool_call_id = tool_call["id"]

            # If tool name does not exist
            if tool_name not in tool_map:

                # Create error result
                tool_result = f"Tool not found: {tool_name}"

            # If tool exists
            else:

                # Get the actual tool object
                selected_tool = tool_map[tool_name]

                # Add tool name to used tool list
                tools_used.append(tool_name)

                # Try running the selected tool
                try:

                    # Run tool with arguments
                    tool_result = selected_tool.invoke(tool_args)

                # If tool fails
                except Exception as error:

                    # Store tool error as text
                    tool_result = f"Tool execution failed: {str(error)}"

            # Create a ToolMessage containing tool result
            tool_message = ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call_id,
                name=tool_name,
            )

            # Add tool result to message history
            messages.append(tool_message)

    # If max tool steps are reached, ask model to summarize with available evidence
    final_message = llm.invoke(
        messages
        + [
            HumanMessage(
                content=(
                    "You reached the maximum number of tool steps. "
                    "Now provide a safe final answer using only the information already gathered."
                )
            )
        ]
    )

    # Return final summarized answer
    return ReActAgentResult(
        answer=final_message.content,
        tools_used=tools_used,
        tool_steps=len(tools_used),
    )