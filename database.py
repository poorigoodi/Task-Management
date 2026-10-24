"""SQLite database layer for the Task Management System."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "tasks.db"

VALID_PRIORITIES = ("Low", "Medium", "High")
VALID_STATUSES = ("Pending", "In Progress", "Completed")


def get_connection() -> sqlite3.Connection:
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    """Create the tasks table if it does not already exist."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High')),
                due_date TEXT,
                status TEXT NOT NULL CHECK (
                    status IN ('Pending', 'In Progress', 'Completed')
                ),
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def add_task(
    title: str,
    description: str | None,
    priority: str,
    due_date: str | None,
    status: str = "Pending",
) -> int:
    """Insert a new task and return its ID."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, priority, due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, description, priority, due_date, status, created_at),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_all_tasks(sort_by: str = "created_at") -> list[sqlite3.Row]:
    """Return all tasks sorted by creation date or due date."""
    order_column = "due_date" if sort_by == "due_date" else "created_at"
    # NULLS LAST style ordering for optional due dates
    if order_column == "due_date":
        order_sql = "ORDER BY (due_date IS NULL), due_date ASC"
    else:
        order_sql = "ORDER BY created_at DESC"

    with get_connection() as conn:
        cursor = conn.execute(f"SELECT * FROM tasks {order_sql}")
        return cursor.fetchall()


def get_task_by_id(task_id: int) -> sqlite3.Row | None:
    """Fetch a single task by ID."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return cursor.fetchone()


def update_task(task_id: int, fields: dict[str, Any]) -> bool:
    """Update one or more fields on a task. Returns True if a row was updated."""
    if not fields:
        return False

    allowed = {"title", "description", "priority", "due_date", "status"}
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return False

    set_clause = ", ".join(f"{column} = ?" for column in updates)
    values = list(updates.values()) + [task_id]

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_task(task_id: int) -> bool:
    """Delete a task by ID. Returns True if a row was deleted."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0


def search_tasks_by_title(query: str) -> list[sqlite3.Row]:
    """Search tasks whose titles contain the query (case-insensitive)."""
    pattern = f"%{query}%"
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM tasks
            WHERE title LIKE ? COLLATE NOCASE
            ORDER BY created_at DESC
            """,
            (pattern,),
        )
        return cursor.fetchall()


def filter_tasks(
    priority: str | None = None,
    status: str | None = None,
) -> list[sqlite3.Row]:
    """Filter tasks by priority and/or status."""
    clauses: list[str] = []
    params: list[str] = []

    if priority:
        clauses.append("priority = ?")
        params.append(priority)
    if status:
        clauses.append("status = ?")
        params.append(status)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_connection() as conn:
        cursor = conn.execute(
            f"SELECT * FROM tasks {where_sql} ORDER BY created_at DESC",
            params,
        )
        return cursor.fetchall()


def get_overdue_tasks() -> list[sqlite3.Row]:
    """Return incomplete tasks with a due date before today."""
    today = date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM tasks
            WHERE due_date IS NOT NULL
              AND due_date < ?
              AND status != 'Completed'
            ORDER BY due_date ASC
            """,
            (today,),
        )
        return cursor.fetchall()


def get_statistics() -> dict[str, int | float]:
    """Compute aggregate task statistics."""
    today = date.today().isoformat()
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        completed = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'Completed'"
        ).fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'Pending'"
        ).fetchone()[0]
        in_progress = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'In Progress'"
        ).fetchone()[0]
        overdue = conn.execute(
            """
            SELECT COUNT(*) FROM tasks
            WHERE due_date IS NOT NULL
              AND due_date < ?
              AND status != 'Completed'
            """,
            (today,),
        ).fetchone()[0]

    completion_percentage = (completed / total * 100) if total else 0.0
    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "in_progress": in_progress,
        "overdue": overdue,
        "completion_percentage": round(completion_percentage, 1),
    }
