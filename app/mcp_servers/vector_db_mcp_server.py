# Import FastMCP to create an MCP server
from mcp.server.fastmcp import FastMCP

# Import the existing vector search tool
from app.tools.vector_search_tool import vector_search_tool


# Create the Vector DB MCP server
mcp = FastMCP("oncoguide-vector-db-mcp")


# Expose vector search as an MCP tool
@mcp.tool()
def search_cancer_vector_db(query: str, top_k: int = 4) -> str:
    """
    Search the local cancer vector database using semantic similarity.
    """

    # Call the existing vector search LangChain tool
    return vector_search_tool.invoke(
        {
            "query": query,
            "top_k": top_k,
        }
    )


# Start the MCP server when this file is run
if __name__ == "__main__":

    # Run the server using stdio transport
    mcp.run()