# Import shutil to delete old vector database folders when rebuilding
import shutil

# Import Path to work with files and folders
from pathlib import Path

# Import Document to store text and metadata
from langchain_core.documents import Document

# Import text splitter to split long documents into small chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import Chroma vector database
from langchain_chroma import Chroma

# Import HuggingFace embeddings
from langchain_huggingface import HuggingFaceEmbeddings

# Import PyPDFLoader to load PDF files
from langchain_community.document_loaders import PyPDFLoader


# Store the folder that contains all source documents
SOURCE_DOCS_DIR = "data/sources"

# Store the folder where Chroma database is saved
CHROMA_DIR = "storage/chroma"

# Store the Chroma collection name
COLLECTION_NAME = "oncoguide_cancer_docs"

# Store the embedding model name
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# Create a function to detect document category from folder path
def get_source_group(file_path: Path) -> str:

    # Get path parts as a list
    parts = list(file_path.parts)

    # If research_papers exists in the path
    if "research_papers" in parts:

        # Find index of research_papers folder
        index = parts.index("research_papers")

        # If there is a subfolder after research_papers
        if len(parts) > index + 1:

            # Return research paper category, for example research_papers/breast
            return f"research_papers/{parts[index + 1]}"

        # Return generic research papers group
        return "research_papers"

    # Return parent folder name for normal sources
    return file_path.parent.name


# Create a function to load markdown files
def load_markdown_file(file_path: Path) -> list[Document]:

    # Read markdown file as text
    text = file_path.read_text(encoding="utf-8")

    # Create document metadata
    metadata = {
        "source": file_path.name,
        "source_group": get_source_group(file_path),
        "file_type": "markdown",
        "path": str(file_path),
    }

    # Return one LangChain document
    return [
        Document(
            page_content=text,
            metadata=metadata,
        )
    ]


# Create a function to load PDF files
def load_pdf_file(file_path: Path) -> list[Document]:

    # Create PDF loader
    loader = PyPDFLoader(str(file_path))

    # Load PDF pages as documents
    documents = loader.load()

    # Loop through each page document
    for document in documents:

        # Add source file name
        document.metadata["source"] = file_path.name

        # Add source group
        document.metadata["source_group"] = get_source_group(file_path)

        # Add file type
        document.metadata["file_type"] = "pdf"

        # Add full file path
        document.metadata["path"] = str(file_path)

        # Rename page metadata safely if available
        document.metadata["page_number"] = document.metadata.get("page", "unknown")

    # Return PDF page documents
    return documents


# Create a function to load all source documents
def load_source_documents() -> list[Document]:

    # Convert source folder to Path object
    source_path = Path(SOURCE_DOCS_DIR)

    # Create empty list for all documents
    all_documents = []

    # Loop through all files inside data/sources
    for file_path in source_path.rglob("*"):

        # Skip folders
        if file_path.is_dir():

            # Continue to next file
            continue

        # If file is markdown
        if file_path.suffix.lower() == ".md":

            # Load markdown document
            documents = load_markdown_file(file_path)

            # Add to all documents
            all_documents.extend(documents)

        # If file is PDF
        elif file_path.suffix.lower() == ".pdf":

            # Load PDF document
            documents = load_pdf_file(file_path)

            # Add to all documents
            all_documents.extend(documents)

    # Return all loaded documents
    return all_documents


# Create a function to clean document text
def clean_document_text(text: str) -> str:

    # Replace multiple spaces with one space
    cleaned = " ".join(text.split())

    # Return cleaned text
    return cleaned


# Create a function to clean all documents
def clean_documents(documents: list[Document]) -> list[Document]:

    # Create empty list for cleaned documents
    cleaned_documents = []

    # Loop through documents
    for document in documents:

        # Clean document text
        cleaned_text = clean_document_text(document.page_content)

        # Skip very short text
        if len(cleaned_text) < 50:

            # Continue to next document
            continue

        # Create cleaned document
        cleaned_document = Document(
            page_content=cleaned_text,
            metadata=document.metadata,
        )

        # Add cleaned document
        cleaned_documents.append(cleaned_document)

    # Return cleaned documents
    return cleaned_documents


# Create a function to split documents into chunks
def split_documents(documents: list[Document]) -> list[Document]:

    # Create recursive text splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
    )

    # Split documents into chunks
    chunks = splitter.split_documents(documents)

    # Return chunks
    return chunks


# Create embedding model
def get_embedding_model() -> HuggingFaceEmbeddings:

    # Create HuggingFace embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME
    )

    # Return embedding model
    return embeddings


# Load Chroma vector store
def get_vector_store() -> Chroma:

    # Create embedding model
    embeddings = get_embedding_model()

    # Create vector store object
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    # Return vector store
    return vector_store


# Build or rebuild RAG index
def build_rag_index(reset: bool = True) -> int:

    # If reset is true and Chroma folder exists
    if reset and Path(CHROMA_DIR).exists():

        # Delete old vector database
        shutil.rmtree(CHROMA_DIR)

    # Load source documents
    documents = load_source_documents()

    # Clean documents
    cleaned_documents = clean_documents(documents)

    # Split documents into chunks
    chunks = split_documents(cleaned_documents)

    # Create embedding model
    embeddings = get_embedding_model()

    # Create Chroma index from chunks
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
    )

    # Return indexed chunk count
    return len(chunks)


# Retrieve relevant documents
def retrieve_context(question: str, top_k: int = 4) -> list[Document]:

    # Load vector store
    vector_store = get_vector_store()

    # Retrieve similar documents
    retrieved_docs = vector_store.similarity_search(
        query=question,
        k=top_k,
    )

    # Return retrieved documents
    return retrieved_docs


# Format retrieved context for LLM
def format_context(documents: list[Document]) -> str:

    # Create empty formatted chunk list
    formatted_chunks = []

    # Loop through retrieved documents
    for index, document in enumerate(documents, start=1):

        # Get source file name
        source = document.metadata.get("source", "unknown source")

        # Get source group
        source_group = document.metadata.get("source_group", "unknown group")

        # Get page number if available
        page_number = document.metadata.get("page_number", "unknown")

        # Format chunk
        formatted_chunk = (
            f"[Source {index}: {source} | Group: {source_group} | Page: {page_number}]\n"
            f"{document.page_content}"
        )

        # Add formatted chunk
        formatted_chunks.append(formatted_chunk)

    # Join chunks
    return "\n\n---\n\n".join(formatted_chunks)