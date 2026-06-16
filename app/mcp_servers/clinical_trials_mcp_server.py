# Import FastMCP to create an MCP server
from mcp.server.fastmcp import FastMCP

# Import the existing ClinicalTrials.gov tool
from app.tools.clinical_trials_tool import clinical_trials_search_tool


# Create the ClinicalTrials MCP server
mcp = FastMCP("oncoguide-clinical-trials-mcp")


# Expose clinical trial search as an MCP tool
@mcp.tool()
def search_clinical_trials(
    condition: str,
    location: str = "",
    max_results: int = 5,
) -> str:
    """
    Search ClinicalTrials.gov for cancer-related clinical trials.
    """

    # Call the existing ClinicalTrials.gov LangChain tool
    return clinical_trials_search_tool.invoke(
        {
            "condition": condition,
            "location": location,
            "max_results": max_results,
        }
    )


# Start the MCP server when this file is run
if __name__ == "__main__":

    # Run the server using stdio transport
    mcp.run()