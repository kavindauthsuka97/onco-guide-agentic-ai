# Import asyncio to run async MCP communication
import asyncio

# Import sys to use the current uv Python executable
import sys

# Import ClientSession for MCP client-server communication
from mcp import ClientSession

# Import StdioServerParameters to launch MCP servers through stdio
from mcp import StdioServerParameters

# Import stdio_client to connect to stdio MCP servers
from mcp.client.stdio import stdio_client


# Convert MCP response content into normal text
def extract_mcp_text(result) -> str:

    # Create empty list to collect text parts
    text_parts = []

    # Loop through every content block in the MCP result
    for item in result.content:

        # If the block has text
        if hasattr(item, "text"):

            # Add text content
            text_parts.append(item.text)

        # If the block does not have text
        else:

            # Convert it to string and add it
            text_parts.append(str(item))

    # Join all text blocks into one string
    return "\n".join(text_parts)


# Async function to call one MCP tool
async def call_mcp_tool_async(
    server_module: str,
    tool_name: str,
    arguments: dict,
) -> str:

    # Define how to start the MCP server
    server_params = StdioServerParameters(
        # Use the current Python executable from the uv environment
        command=sys.executable,

        # Start the MCP server as a Python module
        args=["-m", server_module],
    )

    # Start the MCP server and connect through stdio
    async with stdio_client(server_params) as (read_stream, write_stream):

        # Create an MCP session
        async with ClientSession(read_stream, write_stream) as session:

            # Initialize the MCP session
            await session.initialize()

            # Call the MCP tool by name
            result = await session.call_tool(
                # MCP tool name
                tool_name,

                # MCP tool arguments
                arguments,
            )

            # Return the MCP tool result as plain text
            return extract_mcp_text(result)


# Normal synchronous wrapper for agents
def call_mcp_tool(
    server_module: str,
    tool_name: str,
    arguments: dict,
) -> str:

    # Run the async MCP call from normal Python code
    return asyncio.run(
        call_mcp_tool_async(
            server_module=server_module,
            tool_name=tool_name,
            arguments=arguments,
        )
    )