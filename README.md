# Task Management System

A lightweight Task Management System built with Python and SQLite. Create, organize, update, and track daily tasks from the terminal or a simple Tkinter Todo window — ideal for learning practical Python and showcasing clean CRUD design on GitHub.

## Overview

This application stores tasks in a local SQLite database. You can use either the CLI menu or a Todo-style desktop GUI; both share the same database. Tasks support priorities, optional due dates, status tracking, search/filter, and basic statistics.

## Key Features

- **Add tasks** with title, optional description, priority, optional due date, and status
- **View tasks** in a clean table, sorted by creation date or due date
- **Edit tasks** (title, description, priority, due date, status)
- **Delete tasks** with confirmation
- **Quick status updates** — mark completed, in progress, or reopen as pending
- **Search** by title and **filter** by priority, status, or overdue
- **Statistics** — totals, status breakdown, overdue count, and completion percentage
- **Todo GUI (Tkinter)** — checkbox list to tick tasks done, add/delete, filter Active/Done/All
- **Persistent storage** with SQLite (auto-created on first run)
- **Input validation** with Pydantic and safe parameterized SQL queries

## Technologies

- Python 3.12+
- SQLite (standard library)
- Tkinter (standard library GUI)
- Pydantic 2.x (validation)
- Other standard library modules: `datetime`, `pathlib`, `sqlite3`

## Installation

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/Task-Management.git
cd Task-Management
```

2. Create and activate a virtual environment (recommended):

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### CLI

```bash
python main.py
```

You will see the main menu:

```text
========== TASK MANAGER ==========

1. Add Task
2. View All Tasks
3. Edit Task
4. Delete Task
5. Update Task Status
6. Search Tasks
7. Filter Tasks
8. Task Statistics
0. Exit

Select an option:
```

### Examples

**Add a task**

1. Choose `1`
2. Enter a title (required)
3. Optionally enter a description and due date (`YYYY-MM-DD`)
4. Pick a priority (`Low`, `Medium`, or `High`)

**View and sort**

- Choose `2`, then sort by creation date or due date

**Update status**

- Choose `5`, enter a task ID, then mark it completed / in progress / pending

**Filter overdue tasks**

- Choose `7` → `3` to list incomplete tasks past their due date

**Statistics**

- Choose `8` for totals and completion percentage

### Todo GUI (Tkinter)

```bash
python gui.py
```

- Type a title, pick a priority, press **Add** (or Enter)
- Tick the checkbox to mark a task completed (untick to reopen)
- Switch filters: **Active** / **Done** / **All**
- Use **✕** to delete one task, or **Delete done** to clear completed tasks

The GUI and CLI share the same `tasks.db` file.

## Project Structure

```text
Task-Management/
│
├── main.py            # CLI menu, input handling, validation
├── gui.py             # Tkinter Todo window (check off tasks)
├── database.py        # SQLite connection, schema, CRUD & queries
├── requirements.txt   # Python dependencies
├── README.md          # Project documentation
├── .gitignore         # Ignores DB files, caches, virtualenvs
└── LICENSE            # MIT License
```

| File | Responsibility |
|------|----------------|
| `main.py` | CLI entry point, menu loop, prompts, Pydantic models |
| `gui.py` | Todo-style Tkinter UI with checkboxes |
| `database.py` | Database init, parameterized CRUD, filters, stats |

The SQLite file `tasks.db` is created automatically next to the scripts on first run and is ignored by Git.

## Task Fields

| Field | Details |
|-------|---------|
| ID | Auto-generated integer |
| Title | Required |
| Description | Optional |
| Priority | `Low`, `Medium`, or `High` |
| Due Date | Optional (`YYYY-MM-DD`) |
| Status | `Pending`, `In Progress`, or `Completed` |
| Creation Date | Set automatically |

## Requirements Notes

- Compatible with Windows, macOS, and Linux
- No Django, Flask, FastAPI, auth, or external APIs
- Uses parameterized SQL to reduce SQL injection risk

## License

This project is licensed under the [MIT License](LICENSE).
