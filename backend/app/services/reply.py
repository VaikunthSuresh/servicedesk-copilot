"""Sub-task 5 (optional): draft a user-facing reply from the pipeline outputs."""
from . import llm

SYSTEM = """You are a polite IT service desk agent. Write a short reply (max 120 words) to the employee.
Acknowledge the issue, state the assigned team and priority, give the first 2-3 steps from the suggested
resolution, and say what happens next. No placeholders like [Name]."""


def draft(ticket: str, team: str, priority: str, resolution: str) -> str:
    if llm.available():
        user = f"Ticket: {ticket}\nAssigned team: {team}\nPriority: {priority}\nSuggested resolution:\n{resolution}"
        return llm.chat(SYSTEM, user, max_tokens=250)
    return (
        f"Hi, thanks for reaching out. Your ticket has been routed to {team} with priority {priority}. "
        "An agent will follow up shortly. In the meantime, please try the steps in the suggested resolution."
    )
