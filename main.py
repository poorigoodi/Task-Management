"""Command-line Task Management System."""

from __future__ import annotations

import sys
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

import database as db

DATE_FORMAT = "%Y-%m-%d"
PRIORITY_CHOICES = {
    "1": "Low",
    "2": "Medium",
    "3": "High",
}
STATUS_CHOICES = {
    "1": "Pending",
    "2": "In Progress",
    "3": "Completed",
}


class TaskInput(BaseModel):
    """Validated payload for creating or updating a task."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: str
    due_date: str | None = None
    status: str = "Pending"

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Title cannot be empty.")
        return cleaned

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        if value not in db.VALID_PRIORITIES:
            raise ValueError("Priority must be Low, Medium, or High.")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in db.VALID_STATUSES:
            raise ValueError("Status must be Pending, In Progress, or Completed.")
        return value

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        try:
            parsed = datetime.strptime(value.strip(), DATE_FORMAT).date()
        except ValueError as exc:
            raise ValueError("Due date must use YYYY-MM-DD format.") from exc
        return parsed.isoformat()


def print_header(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 34)
    print(f" {title}")
    print("=" * 34)


def prompt(message: str) -> str:
    """Read a line of user input."""
    try:
        return input(message).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        sys.exit(0)


def prompt_optional(message: str, current: str | None = None) -> str | None:
    """
    Prompt for an optional value.

    Press Enter to keep the current value when editing, or leave blank when creating.
    """
    if current is not None:
        display = current if current else "(empty)"
        value = prompt(f"{message} [{display}]: ")
        if value == "":
            return current
        return value

    value = prompt(f"{message} (optional): ")
    return value if value else None


def choose_from_map(label: str, choices: dict[str, str], current: str | None = None) -> str:
    """Prompt the user to pick a numbered option from a choice map."""
    print(f"\n{label}:")
    for key, value in choices.items():
        marker = " (current)" if current and value == current else ""
        print(f"  {key}. {value}{marker}")

    while True:
        selection = prompt("Select: ")
        if current is not None and selection == "":
            return current
        if selection in choices:
            return choices[selection]
        print("Invalid selection. Please try again.")


def parse_task_id(raw: str) -> int | None:
    """Convert user input into a task ID, or return None if invalid."""
    if not raw.isdigit():
        print("Invalid task ID. Please enter a positive number.")
        return None
    task_id = int(raw)
    if task_id <= 0:
        print("Invalid task ID. Please enter a positive number.")
        return None
    return task_id


def format_cell(value: Any, width: int) -> str:
    """Format a table cell with truncation."""
    text = "-" if value is None or value == "" else str(value)
    if len(text) > width:
        text = text[: width - 3] + "..."
    return text.ljust(width)


def display_tasks(tasks: list[Any], title: str = "Tasks") -> None:
    """Render tasks in a simple ASCII table."""
    print_header(title)
    if not tasks:
        print("No tasks found.")
        return

    headers = ("ID", "Title", "Priority", "Due Date", "Status")
    widths = (4, 28, 10, 12, 12)

    header_row = " | ".join(
        format_cell(header, width) for header, width in zip(headers, widths)
    )
    separator = "-+-".join("-" * width for width in widths)
    print(header_row)
    print(separator)

    for task in tasks:
        row = (
            task["id"],
            task["title"],
            task["priority"],
            task["due_date"],
            task["status"],
        )
        print(
            " | ".join(
                format_cell(value, width) for value, width in zip(row, widths)
            )
        )
    print(f"\nTotal: {len(tasks)} task(s)")


def display_task_details(task: Any) -> None:
    """Print a detailed view of a single task."""
    print()
    print(f"ID:          {task['id']}")
    print(f"Title:       {task['title']}")
    print(f"Description: {task['description'] or '-'}")
    print(f"Priority:    {task['priority']}")
    print(f"Due Date:    {task['due_date'] or '-'}")
    print(f"Status:      {task['status']}")
    print(f"Created At:  {task['created_at']}")


def add_task() -> None:
    """Handle the Add Task menu option."""
    print_header("Add Task")
    title = prompt("Title: ")
    description = prompt_optional("Description")
    priority = choose_from_map("Priority", PRIORITY_CHOICES)
    due_date = prompt_optional("Due date (YYYY-MM-DD)")

    try:
        data = TaskInput(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
        )
    except ValidationError as exc:
        print("Could not create task:")
        for error in exc.errors():
            print(f"  - {error['msg']}")
        return

    task_id = db.add_task(
        title=data.title,
        description=data.description,
        priority=data.priority,
        due_date=data.due_date,
        status=data.status,
    )
    print(f"\nTask #{task_id} created successfully.")


def view_tasks() -> None:
    """Handle the View All Tasks menu option."""
    print_header("View All Tasks")
    print("Sort by:")
    print("  1. Creation date (newest first)")
    print("  2. Due date (earliest first)")
    choice = prompt("Select: ")

    sort_by = "due_date" if choice == "2" else "created_at"
    tasks = db.get_all_tasks(sort_by=sort_by)
    display_tasks(tasks, title="All Tasks")


def edit_task() -> None:
    """Handle the Edit Task menu option."""
    print_header("Edit Task")
    task_id = parse_task_id(prompt("Enter task ID: "))
    if task_id is None:
        return

    task = db.get_task_by_id(task_id)
    if task is None:
        print(f"No task found with ID {task_id}.")
        return

    display_task_details(task)
    print("\nLeave a field blank to keep the current value.")

    title = prompt(f"Title [{task['title']}]: ") or task["title"]
    description = prompt_optional("Description", current=task["description"])
    priority = choose_from_map("Priority", PRIORITY_CHOICES, current=task["priority"])
    due_date = prompt_optional("Due date (YYYY-MM-DD)", current=task["due_date"])
    status = choose_from_map("Status", STATUS_CHOICES, current=task["status"])

    try:
        data = TaskInput(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            status=status,
        )
    except ValidationError as exc:
        print("Could not update task:")
        for error in exc.errors():
            print(f"  - {error['msg']}")
        return

    updated = db.update_task(
        task_id,
        {
            "title": data.title,
            "description": data.description,
            "priority": data.priority,
            "due_date": data.due_date,
            "status": data.status,
        },
    )
    if updated:
        print(f"\nTask #{task_id} updated successfully.")
    else:
        print("No changes were made.")


def delete_task() -> None:
    """Handle the Delete Task menu option."""
    print_header("Delete Task")
    task_id = parse_task_id(prompt("Enter task ID: "))
    if task_id is None:
        return

    task = db.get_task_by_id(task_id)
    if task is None:
        print(f"No task found with ID {task_id}.")
        return

    display_task_details(task)
    confirm = prompt("\nAre you sure you want to delete this task? (y/N): ").lower()
    if confirm != "y":
        print("Deletion cancelled.")
        return

    if db.delete_task(task_id):
        print(f"Task #{task_id} deleted.")
    else:
        print("Could not delete the task.")


def update_task_status() -> None:
    """Handle quick status updates."""
    print_header("Update Task Status")
    task_id = parse_task_id(prompt("Enter task ID: "))
    if task_id is None:
        return

    task = db.get_task_by_id(task_id)
    if task is None:
        print(f"No task found with ID {task_id}.")
        return

    display_task_details(task)
    print("\nChoose a new status:")
    print("  1. Mark as Completed")
    print("  2. Mark as In Progress")
    print("  3. Reopen as Pending")

    choice = prompt("Select: ")
    status_map = {
        "1": "Completed",
        "2": "In Progress",
        "3": "Pending",
    }
    new_status = status_map.get(choice)
    if new_status is None:
        print("Invalid selection.")
        return

    if new_status == task["status"]:
        print(f"Task #{task_id} is already '{new_status}'.")
        return

    db.update_task(task_id, {"status": new_status})
    print(f"\nTask #{task_id} status changed to '{new_status}'.")


def search_tasks() -> None:
    """Handle title search."""
    print_header("Search Tasks")
    query = prompt("Search by title: ")
    if not query:
        print("Search query cannot be empty.")
        return

    tasks = db.search_tasks_by_title(query)
    display_tasks(tasks, title=f"Search Results for '{query}'")


def filter_tasks() -> None:
    """Handle filtering by priority, status, or overdue."""
    print_header("Filter Tasks")
    print("  1. Filter by priority")
    print("  2. Filter by status")
    print("  3. Show overdue tasks")
    choice = prompt("Select: ")

    if choice == "1":
        priority = choose_from_map("Priority", PRIORITY_CHOICES)
        tasks = db.filter_tasks(priority=priority)
        display_tasks(tasks, title=f"Tasks with Priority: {priority}")
    elif choice == "2":
        status = choose_from_map("Status", STATUS_CHOICES)
        tasks = db.filter_tasks(status=status)
        display_tasks(tasks, title=f"Tasks with Status: {status}")
    elif choice == "3":
        tasks = db.get_overdue_tasks()
        display_tasks(tasks, title="Overdue Tasks")
    else:
        print("Invalid selection.")


def show_statistics() -> None:
    """Display aggregate task statistics."""
    print_header("Task Statistics")
    stats = db.get_statistics()
    print(f"Total tasks:        {stats['total']}")
    print(f"Completed:          {stats['completed']}")
    print(f"Pending:            {stats['pending']}")
    print(f"In progress:        {stats['in_progress']}")
    print(f"Overdue:            {stats['overdue']}")
    print(f"Completion rate:    {stats['completion_percentage']}%")
    print(f"Today's date:       {date.today().isoformat()}")


def print_menu() -> None:
    """Show the main CLI menu."""
    print()
    print("========== TASK MANAGER ==========")
    print()
    print("1. Add Task")
    print("2. View All Tasks")
    print("3. Edit Task")
    print("4. Delete Task")
    print("5. Update Task Status")
    print("6. Search Tasks")
    print("7. Filter Tasks")
    print("8. Task Statistics")
    print("0. Exit")
    print()


def main() -> None:
    """Application entry point."""
    db.initialize_database()
    print("Welcome to the Task Management System.")

    actions = {
        "1": add_task,
        "2": view_tasks,
        "3": edit_task,
        "4": delete_task,
        "5": update_task_status,
        "6": search_tasks,
        "7": filter_tasks,
        "8": show_statistics,
    }

    while True:
        print_menu()
        choice = prompt("Select an option: ")
        if choice == "0":
            print("Goodbye!")
            break

        action = actions.get(choice)
        if action is None:
            print("Invalid option. Please choose from the menu.")
            continue

        action()


if __name__ == "__main__":
    main()
