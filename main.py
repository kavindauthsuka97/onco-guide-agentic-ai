# Import load_dotenv to load values from the .env file
from dotenv import load_dotenv

# Load environment variables before importing LangChain/LangGraph code
load_dotenv()

# Import os to read environment variables
import os

# Import uuid to create unique trace/thread IDs
import uuid

# Import Rich Console to print colorful terminal output
from rich.console import Console

# Import Rich Panel to show messages inside nice boxes
from rich.panel import Panel

# Import LangChain HumanMessage to store the user's message
from langchain_core.messages import HumanMessage

# Import RunnableConfig to pass tracing metadata to LangGraph
from langchain_core.runnables import RunnableConfig

# Import our LangGraph chatbot workflow
from app.graph.simple_chat_graph import chat_graph


# Create a Console object for terminal input and output
console = Console()


# Print safe visible execution step
def print_stream_step(node_name: str):

    # Print node execution step
    console.print(f"[dim cyan]Running node:[/dim cyan] [bold]{node_name}[/bold]")


# Create the main function of the program
def main():

    # Read LangSmith tracing value
    langsmith_tracing = os.getenv("LANGSMITH_TRACING", "false")

    # Read LangSmith project name
    langsmith_project = os.getenv("LANGSMITH_PROJECT", "not-set")

    # Create one conversation ID for this terminal session
    conversation_id = str(uuid.uuid4())

    # Show welcome message
    console.print(
        Panel.fit(
            "OncoGuide Agentic AI Chatbot\n"
            "Type 'exit', 'quit', 'stop', or 'end' to stop.\n"
            "Type '/help' to see commands.\n\n"
            f"LangSmith tracing: {langsmith_tracing}\n"
            f"LangSmith project: {langsmith_project}",
            title="OncoGuide",
            style="cyan",
        )
    )

    # Define exit commands
    exit_commands = {
        "exit",
        "quit",
        "stop",
        "end",
        "/exit",
        "/quit",
        "/stop",
        "/end",
    }

    # Start chat loop
    while True:

        # Ask user input
        user_input = console.input("\n[bold green]You:[/bold green] ")

        # Clean user input
        user_input = user_input.strip()

        # Handle empty input
        if not user_input:

            # Show warning
            console.print("[yellow]Please type a message or type 'exit' to stop.[/yellow]")

            # Ask again
            continue

        # Convert command to lowercase
        command = user_input.lower().strip()

        # Stop chatbot
        if command in exit_commands:

            # Show stop message
            console.print(
                Panel.fit(
                    "Goodbye. OncoGuide chatbot stopped.",
                    title="Stopped",
                    style="red",
                )
            )

            # End loop
            break

        # Show help
        if command == "/help":

            # Print help
            console.print(
                Panel(
                    "Available commands:\n\n"
                    "exit / quit / stop / end - Stop the chatbot\n"
                    "/exit / /quit / /stop / /end - Stop the chatbot\n"
                    "/help - Show this help message\n"
                    "/clear - Clear the terminal screen",
                    title="Help",
                    style="blue",
                )
            )

            # Continue loop
            continue

        # Clear screen
        if command == "/clear":

            # Clear terminal
            console.clear()

            # Show title again
            console.print(
                Panel.fit(
                    "OncoGuide Chatbot\nType 'exit', 'quit', 'stop', or 'end' to stop.",
                    title="OncoGuide",
                    style="cyan",
                )
            )

            # Continue loop
            continue

        # Create graph state
        state = {
            "messages": [
                HumanMessage(content=user_input)
            ]
        }

        # Create unique run ID
        run_id = str(uuid.uuid4())

        # Create LangGraph/LangSmith config
        config = RunnableConfig(
            run_name="oncoguide_chat_graph",
            metadata={
                "app": "OncoGuide",
                "conversation_id": conversation_id,
                "run_id": run_id,
                "interface": "terminal",
            },
            configurable={
                "thread_id": conversation_id,
            },
            tags=[
                "oncoguide",
                "terminal",
                "langgraph",
            ],
        )

        # Run safely
        try:

            # Store final state from stream
            final_state = None

            # Stream graph node updates
            for event in chat_graph.stream(
                state,
                config=config,
                stream_mode="updates",
            ):

                # Each event is usually like {"node_name": state_update}
                for node_name, node_output in event.items():

                    # Show visible step
                    print_stream_step(node_name)

                    # Save latest node output if it contains messages
                    if isinstance(node_output, dict) and "messages" in node_output:

                        # Update final state
                        final_state = node_output

            # If no final state was captured
            if final_state is None:

                # Show fallback error
                console.print(
                    Panel(
                        "No final response was returned from the graph.",
                        title="Error",
                        style="red",
                    )
                )

                # Continue chat loop
                continue

            # Get final AI message
            ai_message = final_state["messages"][-1]

            # Display final answer
            console.print(
                Panel(
                    ai_message.content,
                    title="OncoGuide",
                    style="green",
                )
            )

        # Catch errors
        except Exception as error:

            # Display error
            console.print(
                Panel(
                    str(error),
                    title="Error",
                    style="red",
                )
            )


# Run app
if __name__ == "__main__":

    # Start chatbot
    main()