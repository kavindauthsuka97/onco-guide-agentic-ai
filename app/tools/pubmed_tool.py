# Import requests to call PubMed API
import requests

# Import tool decorator so LangChain agents can use this function as a tool
from langchain_core.tools import tool


# Define PubMed search endpoint
PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# Define PubMed summary endpoint
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


# Create PubMed search tool
@tool
def pubmed_search_tool(query: str, max_results: int = 5) -> str:
    """
    Search PubMed for biomedical research papers and return relevant article summaries.
    """

    # Clean user query
    clean_query = query.replace("use pubmed to search", "").strip()

    # If query became empty, use original query
    if not clean_query:

        # Use original query
        clean_query = query

    # Add cancer-related relevance filter when needed
    search_term = f"({clean_query}) AND cancer"

    # Create parameters for PubMed search
    search_params = {
        "db": "pubmed",
        "term": search_term,
        "retmode": "json",
        "retmax": max_results,
        "sort": "relevance",
    }

    # Send request to PubMed search API
    search_response = requests.get(PUBMED_SEARCH_URL, params=search_params, timeout=20)

    # Raise error if API request failed
    search_response.raise_for_status()

    # Convert search response to JSON
    search_data = search_response.json()

    # Extract PubMed IDs
    pubmed_ids = search_data.get("esearchresult", {}).get("idlist", [])

    # If no IDs were found
    if not pubmed_ids:

        # Return no result message
        return "No PubMed results found."

    # Create parameters for PubMed summary request
    summary_params = {
        "db": "pubmed",
        "id": ",".join(pubmed_ids),
        "retmode": "json",
    }

    # Send request to PubMed summary API
    summary_response = requests.get(PUBMED_SUMMARY_URL, params=summary_params, timeout=20)

    # Raise error if API request failed
    summary_response.raise_for_status()

    # Convert summary response to JSON
    summary_data = summary_response.json()

    # Create empty list for formatted results
    results = []

    # Loop through PubMed IDs
    for pubmed_id in pubmed_ids:

        # Get article information
        item = summary_data.get("result", {}).get(pubmed_id, {})

        # Get article title
        title = item.get("title", "No title")

        # Get journal name
        journal = item.get("fulljournalname", "Unknown journal")

        # Get publication date
        pubdate = item.get("pubdate", "Unknown date")

        # Create PubMed URL
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"

        # Format result
        result_text = (
            f"Title: {title}\n"
            f"Journal: {journal}\n"
            f"Date: {pubdate}\n"
            f"URL: {url}"
        )

        # Add result to list
        results.append(result_text)

    # Return all results as text
    return "\n\n---\n\n".join(results)