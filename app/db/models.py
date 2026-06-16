# Import datetime to store timestamps
from datetime import datetime

# Import timezone to store UTC timestamps
from datetime import timezone

# Import SQLAlchemy column types
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Boolean
from sqlalchemy import DateTime

# Import database base class
from app.db.database import Base


# Patient table
class Patient(Base):

    # Table name in database
    __tablename__ = "patients"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Patient ID from frontend or hospital system
    patient_id = Column(String(100), unique=True, index=True, nullable=False)

    # Optional patient display name
    display_name = Column(String(200), nullable=True)

    # Created time
    created_at_utc = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# Conversation table
class Conversation(Base):

    # Table name in database
    __tablename__ = "conversations"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Conversation/session ID
    conversation_id = Column(String(100), unique=True, index=True, nullable=False)

    # Patient ID linked to this conversation
    patient_id = Column(String(100), index=True, nullable=True)

    # Conversation title
    title = Column(String(300), nullable=True)

    # Created time
    created_at_utc = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# Chat message table
class ChatMessage(Base):

    # Table name in database
    __tablename__ = "chat_messages"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Conversation/session ID
    conversation_id = Column(String(100), index=True, nullable=False)

    # Patient ID
    patient_id = Column(String(100), index=True, nullable=True)

    # Message role: user or assistant
    role = Column(String(50), nullable=False)

    # Message content
    content = Column(Text, nullable=False)

    # Selected agent from LangGraph
    selected_agent = Column(String(100), nullable=True)

    # Whether human review was required
    human_review_required = Column(Boolean, default=False)

    # Human review ID if created
    human_review_id = Column(String(100), nullable=True)

    # Created time
    created_at_utc = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )