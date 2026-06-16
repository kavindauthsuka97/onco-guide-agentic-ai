from typing import TypedDict

from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph
from langgraph.graph import END

from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage

from app.utils.llm import get_llm

from app.guardrails.unified_input_guardrail import run_unified_input_guardrail
from app.guardrails.output_guardrail import run_output_guardrail

from app.agents.supervisor_agent import run_supervisor_agent
from app.agents.screening_agent import run_screening_agent
from app.agents.rag_agent import run_rag_agent
from app.agents.clinical_trial_agent import run_clinical_trial_agent
from app.agents.report_explanation_agent import run_report_explanation_agent
from app.agents.react_agent import run_react_agent
from app.agents.manual_tool_agent import run_manual_tool_agent
from app.agents.reflection_agent import run_reflection_agent
from app.agents.claim_verification_agent import run_claim_verification_agent

from app.hitl.review_queue import should_trigger_human_review
from app.hitl.review_queue import create_review_item


class GraphState(TypedDict):
    messages: list[Any]

    input_allowed: bool
    input_risk_level: str
    input_guardrail_reason: str

    route_hint: str

    selected_agent: str
    supervisor_confidence: str
    supervisor_reason: str

    selected_tool: str
    tool_reason: str

    reflection_approved: bool
    reflection_reason: str

    claim_verification_passed: bool
    claim_verification_reason: str

    human_review_required: bool
    human_review_id: str
    human_review_reason: str

    output_approved: bool
    output_guardrail_reason: str


def unified_input_guardrail_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    user_text = messages[-1].content

    guardrail_result = run_unified_input_guardrail(user_text)

    sanitized_messages = [
        HumanMessage(content=guardrail_result.sanitized_message)
    ]

    if not guardrail_result.allowed:
        safety_response = AIMessage(content=guardrail_result.safety_message)

        return {
            "messages": sanitized_messages + [safety_response],
            "input_allowed": False,
            "input_risk_level": guardrail_result.risk_level,
            "input_guardrail_reason": guardrail_result.reason,
            "route_hint": guardrail_result.route_hint,
            "selected_agent": "none",
            "supervisor_confidence": "none",
            "supervisor_reason": "Supervisor skipped because input was blocked.",
            "selected_tool": "",
            "tool_reason": "",
            "reflection_approved": True,
            "reflection_reason": "Reflection skipped because input was blocked.",
            "claim_verification_passed": True,
            "claim_verification_reason": "Claim verification skipped because input was blocked.",
            "human_review_required": False,
            "human_review_id": "",
            "human_review_reason": "Human review skipped because input was blocked.",
            "output_approved": True,
            "output_guardrail_reason": "Output guardrail skipped because input was blocked.",
        }

    return {
        "messages": sanitized_messages,
        "input_allowed": True,
        "input_risk_level": guardrail_result.risk_level,
        "input_guardrail_reason": guardrail_result.reason,
        "route_hint": guardrail_result.route_hint,
        "selected_agent": "",
        "supervisor_confidence": "",
        "supervisor_reason": "",
        "selected_tool": "",
        "tool_reason": "",
        "reflection_approved": False,
        "reflection_reason": "",
        "claim_verification_passed": False,
        "claim_verification_reason": "",
        "human_review_required": False,
        "human_review_id": "",
        "human_review_reason": "",
        "output_approved": False,
        "output_guardrail_reason": "",
    }


def supervisor_node(state: GraphState) -> GraphState:
    user_text = state["messages"][-1].content

    supervisor_result = run_supervisor_agent(
        user_message=user_text,
        route_hint=state["route_hint"],
    )

    return {
        **state,
        "selected_agent": supervisor_result.selected_agent,
        "supervisor_confidence": supervisor_result.confidence,
        "supervisor_reason": supervisor_result.reason,
    }


def route_after_input_guardrail(state: GraphState) -> str:
    if state["input_allowed"]:
        return "supervisor"

    return "end"


def route_after_supervisor(state: GraphState) -> str:
    if state["selected_agent"] == "screening_agent":
        return "screening_agent"

    if state["selected_agent"] == "rag_agent":
        return "rag_agent"

    if state["selected_agent"] == "clinical_trial_agent":
        return "clinical_trial_agent"

    if state["selected_agent"] == "report_explanation_agent":
        return "report_explanation_agent"

    if state["selected_agent"] == "react_agent":
        return "react_agent"

    if state["selected_agent"] == "manual_tool_agent":
        return "manual_tool_agent"

    return "general_chat_agent"


def screening_agent_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    user_text = messages[-1].content

    screening_result = run_screening_agent(user_text)

    answer = (
        "Cancer Symptom Screening Result\n\n"
        f"Risk level: {screening_result.risk_level}\n\n"
        f"Symptoms mentioned: {', '.join(screening_result.symptoms) if screening_result.symptoms else 'Not clearly mentioned'}\n\n"
        f"Red flags: {', '.join(screening_result.red_flags) if screening_result.red_flags else 'No clear red flags detected'}\n\n"
        "Follow-up questions:\n"
        + "\n".join([f"- {question}" for question in screening_result.follow_up_questions])
        + "\n\n"
        f"Doctor summary: {screening_result.doctor_summary}\n\n"
        f"Explanation: {screening_result.explanation}\n\n"
        "Safety note: This is not a diagnosis. Please speak with a qualified healthcare professional for personal medical advice."
    )

    return {
        **state,
        "messages": messages + [AIMessage(content=answer)],
    }


def rag_agent_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    user_text = messages[-1].content

    rag_result = run_rag_agent(user_text)

    return {
        **state,
        "messages": messages + [AIMessage(content=rag_result.answer)],
    }


def clinical_trial_agent_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    user_text = messages[-1].content

    trial_result = run_clinical_trial_agent(user_text)

    return {
        **state,
        "messages": messages + [AIMessage(content=trial_result.answer)],
    }


def report_explanation_agent_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    user_text = messages[-1].content

    report_result = run_report_explanation_agent(user_text)

    return {
        **state,
        "messages": messages + [AIMessage(content=report_result.answer)],
    }


def react_agent_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    user_text = messages[-1].content

    react_result = run_react_agent(user_text)

    answer = (
        f"{react_result.answer}\n\n"
        f"Tools used: {', '.join(react_result.tools_used) if react_result.tools_used else 'No tools used'}\n"
        f"Tool steps: {react_result.tool_steps}"
    )

    return {
        **state,
        "messages": messages + [AIMessage(content=answer)],
        "selected_tool": ", ".join(react_result.tools_used),
        "tool_reason": "Tools selected dynamically by ReAct agent.",
    }


def manual_tool_agent_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    user_text = messages[-1].content

    manual_result = run_manual_tool_agent(user_text)

    answer = (
        f"{manual_result.answer}\n\n"
        "Manual Tool Audit Log\n"
        f"Selected tool: {manual_result.selected_tool}\n"
        f"Reason: {manual_result.tool_reason}"
    )

    return {
        **state,
        "messages": messages + [AIMessage(content=answer)],
        "selected_tool": manual_result.selected_tool,
        "tool_reason": manual_result.tool_reason,
    }


def general_chat_agent_node(state: GraphState) -> GraphState:
    llm = get_llm()
    messages = state["messages"]

    supervisor_context = AIMessage(
        content=(
            f"Supervisor selected: {state['selected_agent']}.\n"
            f"Supervisor reason: {state['supervisor_reason']}.\n\n"
            "Answer safely in simple English. "
            "Do not diagnose. Do not give treatment decisions."
        )
    )

    response = llm.invoke(messages + [supervisor_context])

    return {
        **state,
        "messages": messages + [response],
    }


def reflection_node(state: GraphState) -> GraphState:
    messages = state["messages"]

    user_message = messages[0].content
    draft_answer = messages[-1].content

    reflection_result = run_reflection_agent(
        user_message=user_message,
        draft_answer=draft_answer,
        selected_agent=state["selected_agent"],
    )

    improved_message = AIMessage(content=reflection_result.improved_answer)
    updated_messages = messages[:-1] + [improved_message]

    return {
        **state,
        "messages": updated_messages,
        "reflection_approved": reflection_result.approved,
        "reflection_reason": reflection_result.reason,
    }


def route_after_reflection(state: GraphState) -> str:
    trusted_external_mcp_tools = [
        "pubmed_mcp",
        "clinical_trials_mcp",
        "vector_db_mcp",
    ]

    if state["selected_agent"] == "manual_tool_agent" and state["selected_tool"] in trusted_external_mcp_tools:
        return "output_guardrail"

    return "claim_verification_agent"


def claim_verification_node(state: GraphState) -> GraphState:
    messages = state["messages"]

    user_message = messages[0].content
    reflected_answer = messages[-1].content

    verification_result = run_claim_verification_agent(
        user_message=user_message,
        answer=reflected_answer,
        selected_agent=state["selected_agent"],
    )

    corrected_message = AIMessage(content=verification_result.corrected_answer)
    updated_messages = messages[:-1] + [corrected_message]

    return {
        **state,
        "messages": updated_messages,
        "claim_verification_passed": verification_result.verification_passed,
        "claim_verification_reason": verification_result.reason,
    }


def route_after_claim_verification(state: GraphState) -> str:
    messages = state["messages"]

    user_message = messages[0].content
    answer = messages[-1].content

    needs_review, reason = should_trigger_human_review(
        selected_agent=state["selected_agent"],
        input_risk_level=state["input_risk_level"],
        claim_verification_passed=state["claim_verification_passed"],
        user_message=user_message,
        answer=answer,
    )

    if needs_review:
        return "human_review"

    return "output_guardrail"


def human_review_node(state: GraphState) -> GraphState:
    messages = state["messages"]

    user_message = messages[0].content
    draft_answer = messages[-1].content

    needs_review, reason = should_trigger_human_review(
        selected_agent=state["selected_agent"],
        input_risk_level=state["input_risk_level"],
        claim_verification_passed=state["claim_verification_passed"],
        user_message=user_message,
        answer=draft_answer,
    )

    review_item = create_review_item(
        user_message=user_message,
        draft_answer=draft_answer,
        selected_agent=state["selected_agent"],
        input_risk_level=state["input_risk_level"],
        input_guardrail_reason=state["input_guardrail_reason"],
        supervisor_reason=state["supervisor_reason"],
        reflection_reason=state["reflection_reason"],
        claim_verification_reason=state["claim_verification_reason"],
        human_review_reason=reason,
    )

    pending_message = AIMessage(
        content=(
            "This case has been sent for human review before a final answer is provided.\n\n"
            f"Review ID: {review_item['review_id']}\n"
            f"Reason: {reason}\n\n"
            "A qualified reviewer should approve, edit, or reject the draft response. "
            "For urgent or serious symptoms, please seek medical care immediately."
        )
    )

    updated_messages = messages[:-1] + [pending_message]

    return {
        **state,
        "messages": updated_messages,
        "human_review_required": True,
        "human_review_id": review_item["review_id"],
        "human_review_reason": reason,
    }


def output_guardrail_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    latest_answer = messages[-1].content

    guardrail_result = run_output_guardrail(latest_answer)

    safe_ai_message = AIMessage(content=guardrail_result.final_answer)
    updated_messages = messages[:-1] + [safe_ai_message]

    return {
        **state,
        "messages": updated_messages,
        "output_approved": guardrail_result.approved,
        "output_guardrail_reason": guardrail_result.reason,
    }


graph_builder = StateGraph(GraphState)

graph_builder.add_node("unified_input_guardrail", unified_input_guardrail_node)
graph_builder.add_node("supervisor", supervisor_node)

graph_builder.add_node("screening_agent", screening_agent_node)
graph_builder.add_node("rag_agent", rag_agent_node)
graph_builder.add_node("clinical_trial_agent", clinical_trial_agent_node)
graph_builder.add_node("report_explanation_agent", report_explanation_agent_node)
graph_builder.add_node("react_agent", react_agent_node)
graph_builder.add_node("manual_tool_agent", manual_tool_agent_node)
graph_builder.add_node("general_chat_agent", general_chat_agent_node)

graph_builder.add_node("reflection_agent", reflection_node)
graph_builder.add_node("claim_verification_agent", claim_verification_node)
graph_builder.add_node("human_review", human_review_node)
graph_builder.add_node("output_guardrail", output_guardrail_node)

graph_builder.set_entry_point("unified_input_guardrail")

graph_builder.add_conditional_edges(
    "unified_input_guardrail",
    route_after_input_guardrail,
    {
        "supervisor": "supervisor",
        "end": END,
    },
)

graph_builder.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {
        "screening_agent": "screening_agent",
        "rag_agent": "rag_agent",
        "clinical_trial_agent": "clinical_trial_agent",
        "report_explanation_agent": "report_explanation_agent",
        "react_agent": "react_agent",
        "manual_tool_agent": "manual_tool_agent",
        "general_chat_agent": "general_chat_agent",
    },
)

graph_builder.add_edge("screening_agent", "reflection_agent")
graph_builder.add_edge("rag_agent", "reflection_agent")
graph_builder.add_edge("clinical_trial_agent", "reflection_agent")
graph_builder.add_edge("report_explanation_agent", "reflection_agent")
graph_builder.add_edge("react_agent", "reflection_agent")
graph_builder.add_edge("manual_tool_agent", "reflection_agent")
graph_builder.add_edge("general_chat_agent", "reflection_agent")

graph_builder.add_conditional_edges(
    "reflection_agent",
    route_after_reflection,
    {
        "claim_verification_agent": "claim_verification_agent",
        "output_guardrail": "output_guardrail",
    },
)

graph_builder.add_conditional_edges(
    "claim_verification_agent",
    route_after_claim_verification,
    {
        "human_review": "human_review",
        "output_guardrail": "output_guardrail",
    },
)

graph_builder.add_edge("human_review", END)
graph_builder.add_edge("output_guardrail", END)

chat_graph = graph_builder.compile()


def save_graph_visualization() -> None:
    """
    Saves the LangGraph workflow as a PNG image.

    Output:
        storage/oncoguide_langgraph.png
    """

    output_path = Path("storage/oncoguide_langgraph.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        png_data = chat_graph.get_graph().draw_mermaid_png()
        output_path.write_bytes(png_data)

        print(f"Graph saved successfully: {output_path}")

    except Exception as error:
        fallback_path = Path("storage/oncoguide_langgraph.mmd")
        fallback_path.parent.mkdir(parents=True, exist_ok=True)

        mermaid_code = chat_graph.get_graph().draw_mermaid()
        fallback_path.write_text(mermaid_code, encoding="utf-8")

        print("Could not save PNG graph.")
        print(f"Reason: {error}")
        print(f"Mermaid graph code saved instead: {fallback_path}")


if __name__ == "__main__":
    save_graph_visualization()