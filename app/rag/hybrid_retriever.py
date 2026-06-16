# Import re to clean and tokenize text
import re

# Import Path to work with files and folders
from pathlib import Path

# Import Document to store text with metadata
from langchain_core.documents import Document

# Import BM25Okapi for keyword search
from rank_bm25 import BM25Okapi

# Import PyPDFLoader to read PDF files
from langchain_community.document_loaders import PyPDFLoader

# Import text splitter to split documents into chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import CrossEncoder for re-ranking retrieved chunks
from sentence_transformers import CrossEncoder

# Import vector retrieval from existing Chroma RAG pipeline
from app.rag.basic_rag import retrieve_context

# Import source folder path from basic RAG
from app.rag.basic_rag import SOURCE_DOCS_DIR


# RRF constant
RRF_K = 60

# Cross-encoder model name
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Global reranker cache
_RERANKER = None

# Global BM25 index cache
_BM25_INDEX = None

# Global BM25 documents cache
_BM25_DOCUMENTS = None


# Load cross-encoder only once
def get_reranker() -> CrossEncoder:

    # Use global reranker variable
    global _RERANKER

    # If reranker is not loaded yet
    if _RERANKER is None:

        # Load cross-encoder model
        _RERANKER = CrossEncoder(RERANKER_MODEL_NAME)

    # Return cached reranker
    return _RERANKER


# Decide source group from file path
def get_source_group(file_path: Path) -> str:

    # Convert path into parts
    parts = list(file_path.parts)

    # If file is inside research_papers folder
    if "research_papers" in parts:

        # Get research_papers index
        index = parts.index("research_papers")

        # If category folder exists
        if len(parts) > index + 1:

            # Return category path
            return f"research_papers/{parts[index + 1]}"

        # Return generic group
        return "research_papers"

    # Return parent folder name
    return file_path.parent.name


# Clean text
def clean_text(text: str) -> str:

    # Replace repeated whitespace with single spaces
    cleaned = " ".join(text.split())

    # Return cleaned text
    return cleaned.strip()


# Check noisy chunks
def is_noisy_chunk(text: str) -> bool:

    # Convert to lowercase
    lower_text = text.lower()

    # Common noisy PDF patterns
    noisy_patterns = [
        "references",
        "bibliography",
        "exclusion code",
        "copyright",
        "all rights reserved",
        "doi:",
        "pmid:",
    ]

    # Count noisy patterns
    noisy_count = sum(1 for pattern in noisy_patterns if pattern in lower_text)

    # Skip if many noisy patterns
    if noisy_count >= 2:
        return True

    # Count citation-like patterns
    citation_like_count = len(re.findall(r"\b\d{4};\d+", lower_text))

    # Skip reference-heavy chunks
    if citation_like_count >= 3:
        return True

    # Skip very short chunks
    if len(lower_text) < 80:
        return True

    # Otherwise keep chunk
    return False


# Load text file
def load_text_file(file_path: Path) -> list[Document]:

    # Read text file
    text = file_path.read_text(encoding="utf-8", errors="ignore")

    # Clean text
    cleaned_text = clean_text(text)

    # Skip empty files
    if not cleaned_text:
        return []

    # Create document
    document = Document(
        page_content=cleaned_text,
        metadata={
            "source": file_path.name,
            "source_group": get_source_group(file_path),
            "path": str(file_path),
            "file_type": file_path.suffix.lower().replace(".", ""),
            "page_number": "unknown",
        },
    )

    # Return document list
    return [document]


# Load PDF file
def load_pdf_file(file_path: Path) -> list[Document]:

    # Create PDF loader
    loader = PyPDFLoader(str(file_path))

    # Load PDF pages
    pages = loader.load()

    # Create documents list
    documents = []

    # Loop through PDF pages
    for page in pages:

        # Clean page content
        cleaned_text = clean_text(page.page_content)

        # Skip empty pages
        if not cleaned_text:
            continue

        # Get page number
        page_number = page.metadata.get("page", "unknown")

        # Create page document
        document = Document(
            page_content=cleaned_text,
            metadata={
                "source": file_path.name,
                "source_group": get_source_group(file_path),
                "path": str(file_path),
                "file_type": "pdf",
                "page_number": page_number,
            },
        )

        # Add page document
        documents.append(document)

    # Return PDF documents
    return documents


# Load all source documents
def load_bm25_source_documents() -> list[Document]:

    # Convert source folder to Path
    source_path = Path(SOURCE_DOCS_DIR)

    # Create empty document list
    documents = []

    # Loop through source files
    for file_path in source_path.rglob("*"):

        # Skip folders
        if file_path.is_dir():
            continue

        # Load text and markdown
        if file_path.suffix.lower() in [".md", ".txt"]:
            documents.extend(load_text_file(file_path))

        # Load PDF
        elif file_path.suffix.lower() == ".pdf":
            documents.extend(load_pdf_file(file_path))

    # Return documents
    return documents


# Split documents for BM25
def split_bm25_documents(documents: list[Document]) -> list[Document]:

    # Create text splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
    )

    # Split documents
    chunks = splitter.split_documents(documents)

    # Create cleaned chunks list
    cleaned_chunks = []

    # Loop through chunks
    for chunk in chunks:

        # Clean content
        cleaned_content = clean_text(chunk.page_content)

        # Skip noisy chunks
        if is_noisy_chunk(cleaned_content):
            continue

        # Copy metadata
        metadata = dict(chunk.metadata)

        # Mark BM25 method
        metadata["retrieval_method"] = "bm25"

        # Add cleaned chunk
        cleaned_chunks.append(
            Document(
                page_content=cleaned_content,
                metadata=metadata,
            )
        )

    # Return cleaned chunks
    return cleaned_chunks


# Tokenize text
def tokenize_text(text: str) -> list[str]:

    # Lowercase text
    text = text.lower()

    # Extract words, numbers, and hyphenated terms
    tokens = re.findall(r"[a-zA-Z0-9\-]+", text)

    # Return tokens
    return tokens


# Build or reuse BM25 index
def get_bm25_index() -> tuple[BM25Okapi, list[Document]]:

    # Use global cache variables
    global _BM25_INDEX
    global _BM25_DOCUMENTS

    # If BM25 already exists, reuse it
    if _BM25_INDEX is not None and _BM25_DOCUMENTS is not None:
        return _BM25_INDEX, _BM25_DOCUMENTS

    # Load source documents
    source_documents = load_bm25_source_documents()

    # Split documents into chunks
    corpus_documents = split_bm25_documents(source_documents)

    # Tokenize corpus
    tokenized_corpus = [
        tokenize_text(document.page_content)
        for document in corpus_documents
    ]

    # Build BM25 index
    _BM25_INDEX = BM25Okapi(tokenized_corpus)

    # Cache BM25 documents
    _BM25_DOCUMENTS = corpus_documents

    # Return cached index and documents
    return _BM25_INDEX, _BM25_DOCUMENTS


# Clear BM25 cache manually if documents are updated
def clear_bm25_cache() -> None:

    # Use global cache variables
    global _BM25_INDEX
    global _BM25_DOCUMENTS

    # Clear BM25 index
    _BM25_INDEX = None

    # Clear BM25 documents
    _BM25_DOCUMENTS = None


# Run BM25 retrieval
def bm25_retrieve(query: str, top_k: int = 4) -> list[Document]:

    # Get cached BM25 index and documents
    bm25, corpus_documents = get_bm25_index()

    # If no documents exist
    if not corpus_documents:
        return []

    # Tokenize query
    tokenized_query = tokenize_text(query)

    # Get BM25 scores
    scores = bm25.get_scores(tokenized_query)

    # Sort indexes by score
    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True,
    )

    # Create results list
    results = []

    # Loop through top ranked indexes
    for rank, index in enumerate(ranked_indexes[:top_k], start=1):

        # Skip zero-score results
        if scores[index] <= 0:
            continue

        # Get document
        document = corpus_documents[index]

        # Copy metadata
        metadata = dict(document.metadata)

        # Store BM25 score
        metadata["bm25_score"] = float(scores[index])

        # Store BM25 rank
        metadata["bm25_rank"] = rank

        # Store retrieval method
        metadata["retrieval_method"] = "bm25"

        # Add result document
        results.append(
            Document(
                page_content=document.page_content,
                metadata=metadata,
            )
        )

    # Return results
    return results


# Create document key
def document_key(document: Document) -> str:

    # Get source name
    source = document.metadata.get("source", "unknown")

    # Get page number
    page_number = document.metadata.get("page_number", "")

    # Get content preview
    preview = clean_text(document.page_content[:200])

    # Return unique key
    return f"{source}-{page_number}-{preview}"


# Compute RRF score
def rrf_score(rank: int, k: int = RRF_K) -> float:

    # Return RRF score
    return 1.0 / (k + rank)


# Fuse results using RRF
def fuse_results_rrf(
    vector_docs: list[Document],
    bm25_docs: list[Document],
    max_results: int = 10,
) -> list[Document]:

    # Create fusion map
    fused_map = {}

    # Process vector docs
    for rank, document in enumerate(vector_docs, start=1):

        # Skip noisy chunks
        if is_noisy_chunk(document.page_content):
            continue

        # Create key
        key = document_key(document)

        # Add new document if needed
        if key not in fused_map:

            # Copy metadata
            metadata = dict(document.metadata)

            # Initialize metadata
            metadata["retrieval_method"] = "vector"
            metadata["vector_rank"] = rank
            metadata["bm25_rank"] = None
            metadata["rrf_score"] = 0.0

            # Add to map
            fused_map[key] = {
                "document": Document(
                    page_content=document.page_content,
                    metadata=metadata,
                ),
                "score": 0.0,
                "methods": set(),
            }

        # Add vector RRF score
        fused_map[key]["score"] += rrf_score(rank)

        # Add method
        fused_map[key]["methods"].add("vector")

        # Store vector rank
        fused_map[key]["document"].metadata["vector_rank"] = rank

    # Process BM25 docs
    for rank, document in enumerate(bm25_docs, start=1):

        # Skip noisy chunks
        if is_noisy_chunk(document.page_content):
            continue

        # Create key
        key = document_key(document)

        # Add new document if needed
        if key not in fused_map:

            # Copy metadata
            metadata = dict(document.metadata)

            # Initialize metadata
            metadata["retrieval_method"] = "bm25"
            metadata["vector_rank"] = None
            metadata["bm25_rank"] = rank
            metadata["rrf_score"] = 0.0

            # Add to map
            fused_map[key] = {
                "document": Document(
                    page_content=document.page_content,
                    metadata=metadata,
                ),
                "score": 0.0,
                "methods": set(),
            }

        # Add BM25 RRF score
        fused_map[key]["score"] += rrf_score(rank)

        # Add method
        fused_map[key]["methods"].add("bm25")

        # Store BM25 rank
        fused_map[key]["document"].metadata["bm25_rank"] = rank

    # Convert map to list
    fused_items = list(fused_map.values())

    # Sort by RRF score
    ranked_items = sorted(
        fused_items,
        key=lambda item: item["score"],
        reverse=True,
    )

    # Create final documents list
    final_docs = []

    # Keep top fused results
    for item in ranked_items[:max_results]:

        # Get document
        document = item["document"]

        # Store combined methods
        document.metadata["retrieval_method"] = "+".join(sorted(item["methods"]))

        # Store RRF score
        document.metadata["rrf_score"] = float(item["score"])

        # Add document
        final_docs.append(document)

    # Return final documents
    return final_docs


# Re-rank documents with cross-encoder
def rerank_documents(
    query: str,
    documents: list[Document],
    top_n: int = 6,
) -> list[Document]:

    # Return empty list if no docs
    if not documents:
        return []

    # Load cached reranker
    reranker = get_reranker()

    # Create query-document pairs
    pairs = [
        [query, document.page_content]
        for document in documents
    ]

    # Predict relevance scores
    scores = reranker.predict(pairs)

    # Create scored documents
    scored_docs = []

    # Loop through docs and scores
    for document, score in zip(documents, scores):

        # Copy metadata
        metadata = dict(document.metadata)

        # Add rerank score
        metadata["rerank_score"] = float(score)

        # Add scored document
        scored_docs.append(
            Document(
                page_content=document.page_content,
                metadata=metadata,
            )
        )

    # Sort by rerank score
    ranked_docs = sorted(
        scored_docs,
        key=lambda document: document.metadata.get("rerank_score", 0.0),
        reverse=True,
    )

    # Create final docs
    final_docs = []

    # Add final rank
    for rank, document in enumerate(ranked_docs[:top_n], start=1):

        # Copy metadata
        metadata = dict(document.metadata)

        # Store rerank rank
        metadata["rerank_rank"] = rank

        # Add final document
        final_docs.append(
            Document(
                page_content=document.page_content,
                metadata=metadata,
            )
        )

    # Return final reranked docs
    return final_docs


# Main hybrid retrieval
def hybrid_retrieve(
    query: str,
    top_k: int = 6,
    max_results: int = 6,
) -> list[Document]:

    # Run vector retrieval
    vector_docs = retrieve_context(
        question=query,
        top_k=top_k,
    )

    # Mark vector docs
    marked_vector_docs = []

    # Loop through vector results
    for rank, document in enumerate(vector_docs, start=1):

        # Clean content
        cleaned_content = clean_text(document.page_content)

        # Skip noisy chunks
        if is_noisy_chunk(cleaned_content):
            continue

        # Copy metadata
        metadata = dict(document.metadata)

        # Mark method
        metadata["retrieval_method"] = "vector"

        # Store vector rank
        metadata["vector_rank"] = rank

        # Add vector document
        marked_vector_docs.append(
            Document(
                page_content=cleaned_content,
                metadata=metadata,
            )
        )

    # Run cached BM25 retrieval
    bm25_docs = bm25_retrieve(
        query=query,
        top_k=top_k,
    )

    # Fuse vector and BM25 using RRF
    rrf_candidates = fuse_results_rrf(
        vector_docs=marked_vector_docs,
        bm25_docs=bm25_docs,
        max_results=max(top_k * 2, max_results),
    )

    # Re-rank candidates
    reranked_docs = rerank_documents(
        query=query,
        documents=rrf_candidates,
        top_n=max_results,
    )

    # Return final docs
    return reranked_docs


# Format context for LLM
def format_hybrid_context(documents: list[Document]) -> str:

    # Create formatted chunks
    formatted_chunks = []

    # Loop through documents
    for index, document in enumerate(documents, start=1):

        # Get metadata
        source = document.metadata.get("source", "unknown source")
        source_group = document.metadata.get("source_group", "unknown group")
        page_number = document.metadata.get("page_number", "unknown")
        retrieval_method = document.metadata.get("retrieval_method", "unknown")
        rrf = document.metadata.get("rrf_score", "unknown")
        rerank_score = document.metadata.get("rerank_score", "unknown")
        rerank_rank = document.metadata.get("rerank_rank", "unknown")
        vector_rank = document.metadata.get("vector_rank", "none")
        bm25_rank = document.metadata.get("bm25_rank", "none")

        # Format chunk
        formatted_chunk = (
            f"[Source {index}: {source} | Group: {source_group} | Page: {page_number} | "
            f"Method: {retrieval_method} | RRF: {rrf} | Rerank score: {rerank_score} | "
            f"Rerank rank: {rerank_rank} | Vector rank: {vector_rank} | BM25 rank: {bm25_rank}]\n"
            f"{document.page_content}"
        )

        # Add chunk
        formatted_chunks.append(formatted_chunk)

    # Return joined context
    return "\n\n---\n\n".join(formatted_chunks)