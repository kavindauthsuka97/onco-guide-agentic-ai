# Import Path to work with file paths
from pathlib import Path

# Import tool decorator
from langchain_core.tools import tool

# Import PyPDFLoader for PDF parsing
from langchain_community.document_loaders import PyPDFLoader


# Create report parser tool
@tool
def report_parser_tool(file_path: str) -> str:
    """
    Parse text from a PDF medical report.
    """

    # Convert input path to Path object
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        return f"File not found: {file_path}"

    # Check file is PDF
    if path.suffix.lower() != ".pdf":
        return "Only PDF reports are supported in this stage."

    # Create PDF loader
    loader = PyPDFLoader(str(path))

    # Load PDF pages
    documents = loader.load()

    # Create empty page text list
    page_texts = []

    # Loop through documents
    for document in documents:

        # Get page number
        page_number = document.metadata.get("page", "unknown")

        # Get page content
        content = document.page_content

        # Add page text
        page_texts.append(f"[Page {page_number}]\n{content}")

    # Join all pages
    return "\n\n---\n\n".join(page_texts)