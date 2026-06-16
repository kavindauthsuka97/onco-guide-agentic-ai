# Import tool decorator
from langchain_core.tools import tool

# Import retrieve_context from RAG pipeline
from app.rag.basic_rag import retrieve_context

# Import format_context from RAG pipeline
from app.rag.basic_rag import format_context


# Create vector search tool
@tool
def vector_search_tool(query: str, top_k: int = 4) -> str:
    """
    Search local vector database using semantic similarity.
    """

    # Retrieve relevant documents
    docs = retrieve_context(query, top_k=top_k)

    # If no documents found
    if not docs:
        return "No vector search results found."

    # Format and return context
    return format_context(docs)