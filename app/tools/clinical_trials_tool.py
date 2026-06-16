# Import requests to call ClinicalTrials.gov API
import requests

# Import tool decorator for LangChain tools
from langchain_core.tools import tool


# Store ClinicalTrials.gov API v2 endpoint
CLINICAL_TRIALS_URL = "https://clinicaltrials.gov/api/v2/studies"


# Create clinical trial search tool
@tool
def clinical_trials_search_tool(condition: str, location: str = "", max_results: int = 5) -> str:
    """
    Search ClinicalTrials.gov for cancer-related clinical trials.
    """

    # Create search parameters
    params = {
        "query.cond": condition,
        "pageSize": max_results,
        "format": "json",
    }

    # Add location only if user provided it
    if location:
        params["query.locn"] = location

    # Send request to ClinicalTrials.gov
    response = requests.get(CLINICAL_TRIALS_URL, params=params, timeout=20)

    # Raise error if request failed
    response.raise_for_status()

    # Convert response to JSON
    data = response.json()

    # Get studies list
    studies = data.get("studies", [])

    # If no studies found
    if not studies:
        return "No clinical trials found."

    # Create empty result list
    results = []

    # Loop through studies
    for study in studies:

        # Get protocol section
        protocol = study.get("protocolSection", {})

        # Get identification module
        identification = protocol.get("identificationModule", {})

        # Get status module
        status = protocol.get("statusModule", {})

        # Get design module
        design = protocol.get("designModule", {})

        # Get conditions module
        conditions = protocol.get("conditionsModule", {})

        # Get NCT ID
        nct_id = identification.get("nctId", "Unknown NCT ID")

        # Get brief title
        title = identification.get("briefTitle", "No title")

        # Get overall status
        overall_status = status.get("overallStatus", "Unknown status")

        # Get study phases
        phases = design.get("phases", ["Unknown phase"])

        # Get condition list
        condition_list = conditions.get("conditions", [])

        # Create URL
        url = f"https://clinicaltrials.gov/study/{nct_id}"

        # Format trial result
        result_text = (
            f"NCT ID: {nct_id}\n"
            f"Title: {title}\n"
            f"Status: {overall_status}\n"
            f"Phase: {', '.join(phases)}\n"
            f"Conditions: {', '.join(condition_list)}\n"
            f"URL: {url}\n"
            f"Safety note: This is only a possible trial result. Eligibility must be confirmed by the trial team."
        )

        # Add result
        results.append(result_text)

    # Return all results
    return "\n\n---\n\n".join(results)