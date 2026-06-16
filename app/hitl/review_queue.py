# Import json to read and write review queue data
import json

# Import uuid to create unique review IDs
import uuid

# Import Path to work with file paths
from pathlib import Path

# Import datetime to store created time
from datetime import datetime

# Import timezone to store time in UTC
from datetime import timezone


# Store review queue file path
REVIEW_QUEUE_PATH = Path("storage/hitl_review_queue.json")


# Make sure storage folder exists
REVIEW_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)


# Load all review items from JSON file
def load_review_queue() -> list[dict]:

    # If file does not exist, return empty list
    if not REVIEW_QUEUE_PATH.exists():

        # Return empty review queue
        return []

    # Read file text
    raw_text = REVIEW_QUEUE_PATH.read_text(encoding="utf-8")

    # If file is empty, return empty list
    if not raw_text.strip():

        # Return empty queue
        return []

    # Convert JSON text into Python list
    return json.loads(raw_text)


# Save review queue to JSON file
def save_review_queue(queue: list[dict]) -> None:

    # Write queue data into JSON file
    REVIEW_QUEUE_PATH.write_text(
        # Convert Python list into readable JSON text
        json.dumps(queue, indent=2, ensure_ascii=False),

        # Use UTF-8 encoding
        encoding="utf-8",
    )


# Check if user is asking a low-risk education question
def is_low_risk_educational_question(user_text: str) -> bool:

    # Low-risk educational starters
    educational_starters = [
        "what is",
        "what are",
        "define",
        "meaning of",
        "explain",
        "tell me about",
        "how does",
    ]

    # Low-risk educational terms
    educational_terms = [
        "cancer",
        "lung cancer",
        "breast cancer",
        "colorectal cancer",
        "screening",
        "chemotherapy",
        "radiotherapy",
        "biopsy",
        "tumor",
        "mutation",
        "gene",
        "biomarker",
        "her2",
        "brca",
        "metastasis",
    ]

    # Return true if question starts educationally and contains medical education term
    return (
        any(user_text.startswith(starter) for starter in educational_starters)
        and any(term in user_text for term in educational_terms)
    )


# Check if user is asking for personal medical decision
def is_personal_medical_decision(user_text: str) -> bool:

    # Personal decision phrases
    decision_phrases = [
        "what treatment should i take",
        "which treatment should i choose",
        "should i take",
        "should i stop",
        "can i stop",
        "should i start",
        "what medicine should i take",
        "chemotherapy dose",
        "radiotherapy dose",
        "am i eligible",
        "do i have cancer",
        "is this cancer",
        "what stage am i",
        "how long will i live",
        "survival chance",
        "interpret my mutation",
        "interpret my genetic",
        "my biopsy",
        "my pathology",
        "my report",
        "my scan",
        "my ct",
        "my mri",
        "my pet",
    ]

    # Return true if any personal decision phrase appears
    return any(phrase in user_text for phrase in decision_phrases)


# Check if answer contains unsafe decision wording
def answer_contains_unsafe_decision(answer_text: str) -> bool:

    # Unsafe answer patterns
    unsafe_answer_patterns = [
        "you should take",
        "you should stop",
        "you should start",
        "you are eligible",
        "you have cancer",
        "your cancer is stage",
        "your survival is",
        "the best treatment for you is",
    ]

    # Return true if unsafe answer pattern appears
    return any(pattern in answer_text for pattern in unsafe_answer_patterns)


# Decide whether a case needs human review
def should_trigger_human_review(
    selected_agent: str,
    input_risk_level: str,
    claim_verification_passed: bool,
    user_message: str,
    answer: str,
) -> tuple[bool, str]:

    # Convert user message to lowercase
    user_text = user_message.lower()

    # Convert answer to lowercase
    answer_text = answer.lower()

    # High-risk input should go to human review
    if input_risk_level.lower() in ["high", "red", "urgent"]:

        # Return review decision
        return True, "High-risk or urgent input detected."

    # Report explanation should go to human review
    if selected_agent == "report_explanation_agent":

        # Return review decision
        return True, "Medical report explanation requires human review."

    # Clinical trial matching should go to human review
    if selected_agent == "clinical_trial_agent":

        # Return review decision
        return True, "Clinical trial matching requires human confirmation."

    # Personal medical decision questions should go to human review
    if is_personal_medical_decision(user_text):

        # Return review decision
        return True, "Personal medical decision or personal report interpretation detected."

    # Unsafe final answer wording should go to human review
    if answer_contains_unsafe_decision(answer_text):

        # Return review decision
        return True, "Unsafe personalized medical decision wording detected in answer."

    # Low-risk educational questions should not go to human review if claim verification passed
    if is_low_risk_educational_question(user_text) and claim_verification_passed:

        # Return no review decision
        return False, "Low-risk educational question with verified answer."

    # Failed claim verification should go to human review
    if not claim_verification_passed:

        # Return review decision
        return True, "Claim verification failed or had low confidence."

    # Otherwise human review is not needed
    return False, "Human review not required."


# Create a new review item
def create_review_item(
    user_message: str,
    draft_answer: str,
    selected_agent: str,
    input_risk_level: str,
    input_guardrail_reason: str,
    supervisor_reason: str,
    reflection_reason: str,
    claim_verification_reason: str,
    human_review_reason: str,
) -> dict:

    # Create unique review ID
    review_id = str(uuid.uuid4())

    # Create review item dictionary
    review_item = {
        "review_id": review_id,
        "status": "pending",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selected_agent": selected_agent,
        "input_risk_level": input_risk_level,
        "input_guardrail_reason": input_guardrail_reason,
        "supervisor_reason": supervisor_reason,
        "reflection_reason": reflection_reason,
        "claim_verification_reason": claim_verification_reason,
        "human_review_reason": human_review_reason,
        "user_message": user_message,
        "draft_answer": draft_answer,
        "reviewer_decision": "",
        "reviewer_comment": "",
        "final_answer": "",
    }

    # Load current queue
    queue = load_review_queue()

    # Add new item
    queue.append(review_item)

    # Save queue
    save_review_queue(queue)

    # Return created review item
    return review_item


# Update review item status
def update_review_item(
    review_id: str,
    status: str,
    reviewer_comment: str = "",
    final_answer: str = "",
) -> bool:

    # Load current queue
    queue = load_review_queue()

    # Loop through queue items
    for item in queue:

        # Find matching review item
        if item["review_id"] == review_id:

            # Update status
            item["status"] = status

            # Update reviewer decision
            item["reviewer_decision"] = status

            # Update reviewer comment
            item["reviewer_comment"] = reviewer_comment

            # Update final answer
            item["final_answer"] = final_answer

            # Update time
            item["reviewed_at_utc"] = datetime.now(timezone.utc).isoformat()

            # Save queue
            save_review_queue(queue)

            # Return success
            return True

    # Return false if review item not found
    return False