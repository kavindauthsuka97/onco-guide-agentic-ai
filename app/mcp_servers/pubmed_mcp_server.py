# Import FastMCP to create an MCP server
from mcp.server.fastmcp import FastMCP

# Import the existing PubMed tool
from app.tools.pubmed_tool import pubmed_search_tool


# Create the PubMed MCP server
mcp = FastMCP("oncoguide-pubmed-mcp")


# Expose PubMed search as an MCP tool
@mcp.tool()
def search_pubmed(query: str, max_results: int = 5) -> str:
    """
    Search PubMed for biomedical research papers.
    """

    # Call the existing PubMed LangChain tool
    return pubmed_search_tool.invoke(
        {
            "query": query,
            "max_results": max_results,
        }
    )


# Start the MCP server when this file is run
if __name__ == "__main__":

    # Run the server using stdio transport
    mcp.run()