# Import Path to read local documents
from pathlib import Path

# Import tool decorator
from langchain_core.tools import tool

# Import BM25Okapi for keyword search
from rank_bm25 import BM25Okapi


# Define source folder
SOURCE_DOCS_DIR = "data/sources"


# Create helper function to load local text files
def load_text_corpus() -> list[dict]:
    """
    Load markdown and text files for BM25 keyword search.
    """

    # Create source path
    source_path = Path(SOURCE_DOCS_DIR)

    # Create empty corpus list
    corpus = []

    # Loop through markdown and text files
    for file_path in list(source_path.rglob("*.md")) + list(source_path.rglob("*.txt")):

        # Read text
        text = file_path.read_text(encoding="utf-8")

        # Add document to corpus
        corpus.append(
            {
                "source": file_path.name,
                "path": str(file_path),
                "text": text,
            }
        )

    # Return corpus
    return corpus


# Create BM25 keyword search tool
@tool
def bm25_search_tool(query: str, top_k: int = 4) -> str:
    """
    Search local markdown and text documents using BM25 keyword search.
    """

    # Load corpus
    corpus = load_text_corpus()

    # If corpus is empty
    if not corpus:
        return "No markdown/text corpus found for BM25 search."

    # Tokenize documents
    tokenized_corpus = [doc["text"].lower().split() for doc in corpus]

    # Create BM25 index
    bm25 = BM25Okapi(tokenized_corpus)

    # Tokenize query
    tokenized_query = query.lower().split()

    # Get scores
    scores = bm25.get_scores(tokenized_query)

    # Sort indexes by score
    ranked_indexes = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    # Create results list
    results = []

    # Loop through top ranked documents
    for index in ranked_indexes[:top_k]:

        # Get document
        doc = corpus[index]

        # Get score
        score = scores[index]

        # Format result
        result = (
            f"Source: {doc['source']}\n"
            f"Score: {score}\n"
            f"Text preview: {doc['text'][:700]}"
        )

        # Add result
        results.append(result)

    # Return results
    return "\n\n---\n\n".join(results)