# Import real MCP client caller
from app.mcp_servers.mcp_client import call_mcp_tool


# Call PubMed through real MCP client-server flow
def call_pubmed_mcp(query: str, max_results: int = 5) -> str:

    # Call PubMed MCP server
    return call_mcp_tool(
        server_module="app.mcp_servers.pubmed_mcp_server",
        tool_name="search_pubmed",
        arguments={
            "query": query,
            "max_results": max_results,
        },
    )


# Call ClinicalTrials.gov through real MCP client-server flow
def call_clinical_trials_mcp(
    condition: str,
    location: str = "",
    max_results: int = 5,
) -> str:

    # Call ClinicalTrials MCP server
    return call_mcp_tool(
        server_module="app.mcp_servers.clinical_trials_mcp_server",
        tool_name="search_clinical_trials",
        arguments={
            "condition": condition,
            "location": location,
            "max_results": max_results,
        },
    )


# Call local vector database through real MCP client-server flow
def call_vector_db_mcp(query: str, top_k: int = 4) -> str:

    # Call Vector DB MCP server
    return call_mcp_tool(
        server_module="app.mcp_servers.vector_db_mcp_server",
        tool_name="search_cancer_vector_db",
        arguments={
            "query": query,
            "top_k": top_k,
        },
    )