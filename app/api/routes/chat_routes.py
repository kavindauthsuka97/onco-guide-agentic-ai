import json
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from app.api.schemas import ChatRequest, ChatResponse
from app.graph.simple_chat_graph import chat_graph


router = APIRouter()


def create_graph_state(message: str) -> dict:
    return {
        "messages": [
            HumanMessage(content=message)
        ]
    }


def create_graph_config(conversation_id: str, interface: str) -> RunnableConfig:
    run_id = str(uuid.uuid4())

    return RunnableConfig(
        run_name=f"oncoguide_{interface}_chat_graph",
        metadata={
            "app": "OncoGuide",
            "interface": interface,
            "conversation_id": conversation_id,
            "run_id": run_id,
        },
        configurable={
            "thread_id": conversation_id,
        },
        tags=[
            "oncoguide",
            interface,
            "langgraph",
        ],
    )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    state = create_graph_state(request.message)

    config = create_graph_config(
        conversation_id=conversation_id,
        interface="fastapi",
    )

    try:
        result = chat_graph.invoke(
            state,
            config=config,
        )

        ai_message = result["messages"][-1]

        return ChatResponse(
            success=True,
            answer=ai_message.content,
            conversation_id=conversation_id,
            selected_agent=result.get("selected_agent"),
            human_review_required=result.get("human_review_required"),
            human_review_id=result.get("human_review_id"),
            error=None,
        )

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "answer": "",
                "conversation_id": conversation_id,
                "error": str(error),
            },
        )


def sse_event(event_type: str, data: dict) -> str:
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {json_data}\n\n"


def stream_chat_events(request: ChatRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    state = create_graph_state(request.message)

    config = create_graph_config(
        conversation_id=conversation_id,
        interface="fastapi_stream",
    )

    yield sse_event(
        "start",
        {
            "conversation_id": conversation_id,
            "message": "Chat started.",
        },
    )

    final_state = None

    try:
        for event in chat_graph.stream(
            state,
            config=config,
            stream_mode="updates",
        ):
            for node_name, node_output in event.items():
                yield sse_event(
                    "progress",
                    {
                        "node": node_name,
                        "message": f"Running {node_name}",
                    },
                )

                if isinstance(node_output, dict) and "messages" in node_output:
                    final_state = node_output

        if final_state is None:
            yield sse_event(
                "error",
                {
                    "message": "No final response returned from graph.",
                    "conversation_id": conversation_id,
                },
            )
            return

        ai_message = final_state["messages"][-1]

        yield sse_event(
            "final",
            {
                "success": True,
                "answer": ai_message.content,
                "conversation_id": conversation_id,
                "selected_agent": final_state.get("selected_agent"),
                "human_review_required": final_state.get("human_review_required"),
                "human_review_id": final_state.get("human_review_id"),
            },
        )

    except Exception as error:
        yield sse_event(
            "error",
            {
                "success": False,
                "message": str(error),
                "conversation_id": conversation_id,
            },
        )


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    return StreamingResponse(
        stream_chat_events(request),
        media_type="text/event-stream",
    )