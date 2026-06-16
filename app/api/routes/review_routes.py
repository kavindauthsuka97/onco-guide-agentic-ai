# Import APIRouter for route grouping
from fastapi import APIRouter

# Import schemas
from app.api.schemas import ReviewDecisionRequest
from app.api.schemas import ReviewEditApproveRequest
from app.api.schemas import ReviewDecisionResponse

# Import HITL queue functions
from app.hitl.review_queue import load_review_queue
from app.hitl.review_queue import update_review_item


# Create router
router = APIRouter(
    prefix="/review",
    tags=["Human Review"],
)


# Get pending review items
@router.get("/pending")
def get_pending_reviews():

    # Load review queue
    queue = load_review_queue()

    # Filter pending items
    pending_items = [
        item for item in queue
        if item.get("status") == "pending"
    ]

    # Return pending reviews
    return {
        "success": True,
        "count": len(pending_items),
        "items": pending_items,
    }


# Get all review items
@router.get("/all")
def get_all_reviews():

    # Load review queue
    queue = load_review_queue()

    # Return all items
    return {
        "success": True,
        "count": len(queue),
        "items": queue,
    }


# Approve review item
@router.post("/approve", response_model=ReviewDecisionResponse)
def approve_review(request: ReviewDecisionRequest):

    # Update review status
    success = update_review_item(
        review_id=request.review_id,
        status="approved",
        reviewer_comment=request.comment or "Approved by human reviewer.",
        final_answer="",
    )

    # Return not found response
    if not success:
        return ReviewDecisionResponse(
            success=False,
            message="Review ID not found.",
        )

    # Return success response
    return ReviewDecisionResponse(
        success=True,
        message="Review approved.",
    )


# Reject review item
@router.post("/reject", response_model=ReviewDecisionResponse)
def reject_review(request: ReviewDecisionRequest):

    # Update review status
    success = update_review_item(
        review_id=request.review_id,
        status="rejected",
        reviewer_comment=request.comment or "Rejected by human reviewer.",
        final_answer="",
    )

    # Return not found response
    if not success:
        return ReviewDecisionResponse(
            success=False,
            message="Review ID not found.",
        )

    # Return success response
    return ReviewDecisionResponse(
        success=True,
        message="Review rejected.",
    )


# Edit and approve review item
@router.post("/edit-approve", response_model=ReviewDecisionResponse)
def edit_approve_review(request: ReviewEditApproveRequest):

    # Update review status
    success = update_review_item(
        review_id=request.review_id,
        status="edited_approved",
        reviewer_comment=request.comment or "Edited and approved.",
        final_answer=request.final_answer,
    )

    # Return not found response
    if not success:
        return ReviewDecisionResponse(
            success=False,
            message="Review ID not found.",
        )

    # Return success response
    return ReviewDecisionResponse(
        success=True,
        message="Review edited and approved.",
    )