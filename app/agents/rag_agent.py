# Import json to parse LLM JSON outputs
import json

# Import BaseModel to define structured RAG output
from pydantic import BaseModel

# Import Document because retrieved chunks are LangChain documents
from langchain_core.documents import Document

# Import call_llm to call Groq through LangChain
from app.utils.llm import call_llm

# Import hybrid retrieval
from app.rag.hybrid_retriever import hybrid_retrieve

# Import hybrid context formatter
from app.rag.hybrid_retriever import format_hybrid_context


# Define final RAG result structure
class RAGResult(BaseModel):

    # Store final answer text
    answer: str

    # Store sources used by the answer
    sources: list[str]

    # Store final RAG status
    status: str


# Rewrite the user question into a clearer search query
def rewrite_question(user_question: str) -> str:

    # Create system prompt for question rewriting
    system_prompt = """
    You are a medical RAG query rewriting assistant.
    Rewrite the user's question into a clear search query for trusted cancer documents.
    Keep the meaning same.
    Return only the rewritten question.
    """

    # Create user prompt
    user_prompt = f"User question: {user_question}"

    # Call LLM
    rewritten_question = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    # Return cleaned rewritten question
    return rewritten_question.strip()


# Classify whether the question is suitable for cancer RAG
def classify_question(question: str) -> dict:

    # Create system prompt for classification
    system_prompt = """
    You are a cancer RAG question classifier.

    Return ONLY valid JSON:
    {
      "category": "cancer_related" or "off_topic",
      "reason": "short reason"
    }

    Cancer-related includes:
    symptoms, cancer education, screening, diagnosis explanation, cancer reports,
    clinical trials, oncology terms, cancer risk, cancer treatment education.

    Off-topic includes:
    programming, politics, sports, finance, travel, unrelated general questions.
    """

    # Create user prompt
    user_prompt = f"Question: {question}"

    # Call LLM
    raw_response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    # Try parsing JSON
    try:

        # Convert response into dictionary
        return json.loads(raw_response)

    # If JSON fails, use safe fallback
    except Exception:

        # Return cancer-related fallback
        return {
            "category": "cancer_related",
            "reason": "Fallback classification used.",
        }


# Grade retrieved documents
def grade_retrieval(question: str, docs: list[Document]) -> dict:

    # Format retrieved context
    context = format_hybrid_context(docs)

    # Create system prompt for retrieval grading
    system_prompt = """
    You are a medical RAG retrieval grader.

    Decide whether the retrieved context is enough to answer the question.

    Return ONLY valid JSON:
    {
      "decision": "generate_answer" or "refine_question" or "cannot_answer",
      "reason": "short reason"
    }

    Rules:
    - generate_answer: context directly answers the question.
    - refine_question: context is weak but question can be improved and retried.
    - cannot_answer: context is not useful or trusted context is missing.
    """

    # Create user prompt
    user_prompt = f"""
    Question:
    {question}

    Retrieved context:
    {context}
    """

    # Call LLM
    raw_response = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    # Try parsing JSON
    try:

        # Convert response into dictionary
        return json.loads(raw_response)

    # If parsing fails
    except Exception:

        # Default to generate if docs exist
        if docs:

            # Return fallback generate decision
            return {
                "decision": "generate_answer",
                "reason": "Fallback grading used because documents were retrieved.",
            }

        # Cannot answer if no docs
        return {
            "decision": "cannot_answer",
            "reason": "No retrieved documents.",
        }


# Refine question when retrieval is weak
def refine_question(question: str) -> str:

    # Create system prompt
    system_prompt = """
    You are a medical search query refinement assistant.
    Make the question more specific for cancer document retrieval.
    Return only the refined question.
    """

    # Create user prompt
    user_prompt = f"Question: {question}"

    # Call LLM
    refined_question = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    # Return cleaned refined question
    return refined_question.strip()


# Generate final answer from retrieved context
def generate_answer(original_question: str, docs: list[Document]) -> RAGResult:

    # Format retrieved context
    context = format_hybrid_context(docs)

    # Extract source names
    sources = [
        doc.metadata.get("source", "unknown source")
        for doc in docs
    ]

    # Create system prompt
    system_prompt = """
    You are OncoGuide, an evidence-based cancer education assistant.

    Use ONLY the trusted context.

    Rules:
    - Do not diagnose cancer.
    - Do not give treatment decisions.
    - Do not claim the user has cancer.
    - Use simple English.
    - Mention uncertainty when needed.
    - Recommend speaking with a doctor or qualified healthcare professional.
    - If context is insufficient, say you do not have enough trusted information.
    - Include source names when you answer.
    """

    # Create user prompt
    user_prompt = f"""
    User question:
    {original_question}

    Trusted hybrid retrieval context:
    {context}

    Answer using only the trusted context.
    """

    # Call LLM
    answer = call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
    )

    # Add source list
    answer_with_sources = (
        f"{answer}\n\n"
        f"Sources used: {', '.join(sorted(set(sources)))}"
    )

    # Return final result
    return RAGResult(
        answer=answer_with_sources,
        sources=sources,
        status="answered",
    )


# Generate off-topic response
def off_topic_response(question: str) -> RAGResult:

    # Return safe off-topic message
    return RAGResult(
        answer=(
            "This question seems outside my cancer-related medical knowledge scope. "
            "Please ask a cancer screening, cancer education, medical report, or clinical-trial-related question."
        ),
        sources=[],
        status="off_topic",
    )


# Generate cannot-answer response
def cannot_answer_response(question: str) -> RAGResult:

    # Return safe cannot-answer message
    return RAGResult(
        answer=(
            "I do not have enough trusted cancer information in the current knowledge base to answer this safely. "
            "Please ask a doctor or qualified healthcare professional for personal medical advice."
        ),
        sources=[],
        status="cannot_answer",
    )


# Main agentic RAG function
def run_rag_agent(user_message: str) -> RAGResult:

    # Rewrite original user question
    rewritten_question = rewrite_question(user_message)

    # Classify rewritten question
    classification = classify_question(rewritten_question)

    # If question is off-topic
    if classification.get("category") == "off_topic":

        # Return off-topic response
        return off_topic_response(user_message)

    # Retrieve documents using hybrid search
    docs = hybrid_retrieve(
        query=rewritten_question,
        top_k=4,
        max_results=6,
    )

    # Grade retrieved documents
    grade = grade_retrieval(rewritten_question, docs)

    # Get retrieval decision
    decision = grade.get("decision", "generate_answer")

    # If retrieval is good
    if decision == "generate_answer":

        # Return generated answer
        return generate_answer(user_message, docs)

    # If question should be refined
    if decision == "refine_question":

        # Refine the rewritten question
        refined = refine_question(rewritten_question)

        # Retrieve again using hybrid search
        refined_docs = hybrid_retrieve(
            query=refined,
            top_k=4,
            max_results=6,
        )

        # Grade refined retrieval
        refined_grade = grade_retrieval(refined, refined_docs)

        # If refined retrieval is good
        if refined_grade.get("decision") == "generate_answer":

            # Generate answer from refined docs
            return generate_answer(user_message, refined_docs)

        # Otherwise cannot answer
        return cannot_answer_response(user_message)

    # If retrieval cannot answer
    return cannot_answer_response(user_message)