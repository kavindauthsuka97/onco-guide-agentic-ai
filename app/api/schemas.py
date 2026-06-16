from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    success: bool
    answer: str
    conversation_id: str
    selected_agent: str | None = None
    human_review_required: bool | None = None
    human_review_id: str | None = None
    error: str | None = None


class ReviewDecisionRequest(BaseModel):
    review_id: str
    comment: str | None = ""


class ReviewEditApproveRequest(BaseModel):
    review_id: str
    final_answer: str
    comment: str | None = "Edited and approved."


class ReviewDecisionResponse(BaseModel):
    success: bool
    message: str