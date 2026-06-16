# Import SQLAlchemy Session type
from sqlalchemy.orm import Session

# Import database models
from app.db.models import Patient
from app.db.models import Conversation
from app.db.models import ChatMessage


# Get or create patient
def get_or_create_patient(
    db: Session,
    patient_id: str,
    display_name: str | None = None,
) -> Patient:

    # Search patient by patient_id
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()

    # If patient exists, return it
    if patient:
        return patient

    # Create new patient
    patient = Patient(
        patient_id=patient_id,
        display_name=display_name,
    )

    # Add patient to database
    db.add(patient)

    # Save changes
    db.commit()

    # Refresh object
    db.refresh(patient)

    # Return created patient
    return patient


# Get or create conversation
def get_or_create_conversation(
    db: Session,
    conversation_id: str,
    patient_id: str | None = None,
    title: str | None = None,
) -> Conversation:

    # Search conversation by conversation_id
    conversation = (
        db.query(Conversation)
        .filter(Conversation.conversation_id == conversation_id)
        .first()
    )

    # If conversation exists, return it
    if conversation:
        return conversation

    # Create new conversation
    conversation = Conversation(
        conversation_id=conversation_id,
        patient_id=patient_id,
        title=title,
    )

    # Add conversation to database
    db.add(conversation)

    # Save changes
    db.commit()

    # Refresh object
    db.refresh(conversation)

    # Return created conversation
    return conversation


# Save one chat message
def save_chat_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    patient_id: str | None = None,
    selected_agent: str | None = None,
    human_review_required: bool = False,
    human_review_id: str | None = None,
) -> ChatMessage:

    # Create chat message row
    chat_message = ChatMessage(
        conversation_id=conversation_id,
        patient_id=patient_id,
        role=role,
        content=content,
        selected_agent=selected_agent,
        human_review_required=human_review_required,
        human_review_id=human_review_id,
    )

    # Add message to database
    db.add(chat_message)

    # Save changes
    db.commit()

    # Refresh object
    db.refresh(chat_message)

    # Return saved message
    return chat_message


# Get chat history for a conversation
def get_chat_history(
    db: Session,
    conversation_id: str,
) -> list[ChatMessage]:

    # Query messages by conversation ID
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at_utc.asc())
        .all()
    )

    # Return messages
    return messages