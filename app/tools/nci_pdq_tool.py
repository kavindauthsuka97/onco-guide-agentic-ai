# Import tool decorator for LangChain tools
from langchain_core.tools import tool

# Import retrieve_context from our RAG pipeline
from app.rag.basic_rag import retrieve_context

# Import format_context from our RAG pipeline
from app.rag.basic_rag import format_context


# Create local NCI PDQ search tool
@tool
def nci_pdq_search_tool(query: str, top_k: int = 4) -> str:
    """
    Search local NCI PDQ cancer documents from the vector database.
    """

    # Retrieve relevant documents from local vector database
    docs = retrieve_context(query, top_k=top_k)

    # Keep only NCI PDQ documents if possible
    nci_docs = [
        doc for doc in docs
        if "nci" in doc.metadata.get("source_group", "").lower()
        or "pdq" in doc.metadata.get("source_group", "").lower()
        or "nci" in doc.metadata.get("source", "").lower()
        or "pdq" in doc.metadata.get("source", "").lower()
    ]

    # Use NCI-filtered docs if available, otherwise use retrieved docs
    final_docs = nci_docs if nci_docs else docs

    # If no documents found
    if not final_docs:
        return "No NCI PDQ content found in the local knowledge base."

    # Format documents into context
    return format_context(final_docs)