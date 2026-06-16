# Import typer to build a small command-line reviewer app
import typer

# Import Console for colorful terminal output
from rich.console import Console

# Import Panel to show review details nicely
from rich.panel import Panel

# Import queue functions
from app.hitl.review_queue import load_review_queue
from app.hitl.review_queue import update_review_item


# Create Typer app
app = typer.Typer()

# Create Rich console
console = Console()


# List pending review items
@app.command()
def list_pending():

    # Load review queue
    queue = load_review_queue()

    # Filter pending items
    pending_items = [item for item in queue if item["status"] == "pending"]

    # If no pending items
    if not pending_items:

        # Print message
        console.print("[green]No pending review items.[/green]")

        # Stop function
        return

    # Loop through pending items
    for item in pending_items:

        # Print review summary
        console.print(
            Panel(
                f"Review ID: {item['review_id']}\n"
                f"Agent: {item['selected_agent']}\n"
                f"Risk: {item['input_risk_level']}\n"
                f"Reason: {item['human_review_reason']}\n\n"
                f"User message:\n{item['user_message']}\n\n"
                f"Draft answer:\n{item['draft_answer']}",
                title="Pending Human Review",
                style="yellow",
            )
        )


# Approve a review item
@app.command()
def approve(review_id: str):

    # Update item as approved
    success = update_review_item(
        review_id=review_id,
        status="approved",
        reviewer_comment="Approved by human reviewer.",
        final_answer="",
    )

    # Print result
    console.print("[green]Approved.[/green]" if success else "[red]Review ID not found.[/red]")


# Reject a review item
@app.command()
def reject(review_id: str, comment: str = "Rejected by human reviewer."):

    # Update item as rejected
    success = update_review_item(
        review_id=review_id,
        status="rejected",
        reviewer_comment=comment,
        final_answer="",
    )

    # Print result
    console.print("[green]Rejected.[/green]" if success else "[red]Review ID not found.[/red]")


# Edit and approve a review item
@app.command()
def edit_approve(review_id: str, final_answer: str, comment: str = "Edited and approved."):

    # Update item as edited and approved
    success = update_review_item(
        review_id=review_id,
        status="edited_approved",
        reviewer_comment=comment,
        final_answer=final_answer,
    )

    # Print result
    console.print("[green]Edited and approved.[/green]" if success else "[red]Review ID not found.[/red]")


# Run Typer app
if __name__ == "__main__":

    # Start reviewer CLI
    app()