"""Tkinter Todo GUI for the Task Management System."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import database as db


class TodoApp(tk.Tk):
    """Simple todo-style window with checkboxes and shared SQLite storage."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Todo — Task Manager")
        self.geometry("520x640")
        self.minsize(420, 480)
        self.configure(bg="#f4f5f7")

        self.filter_var = tk.StringVar(value="active")
        self.priority_var = tk.StringVar(value="Medium")
        self._check_vars: dict[int, tk.BooleanVar] = {}

        self._build_styles()
        self._build_ui()
        db.initialize_database()
        self.refresh_tasks()

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Card.TFrame", background="#ffffff")
        style.configure("App.TFrame", background="#f4f5f7")
        style.configure("Title.TLabel", background="#f4f5f7", font=("Segoe UI", 18, "bold"))
        style.configure("Sub.TLabel", background="#f4f5f7", foreground="#5f6368", font=("Segoe UI", 10))
        style.configure("Task.TCheckbutton", background="#ffffff", font=("Segoe UI", 11))
        style.configure("Meta.TLabel", background="#ffffff", foreground="#80868b", font=("Segoe UI", 9))
        style.configure("Stats.TLabel", background="#f4f5f7", font=("Segoe UI", 10))

    def _build_ui(self) -> None:
        root = ttk.Frame(self, style="App.TFrame", padding=16)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root, style="App.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="My Tasks", style="Title.TLabel").pack(anchor="w")
        self.stats_label = ttk.Label(header, text="", style="Sub.TLabel")
        self.stats_label.pack(anchor="w", pady=(2, 12))

        # Add task row
        add_card = ttk.Frame(root, style="Card.TFrame", padding=12)
        add_card.pack(fill="x", pady=(0, 12))

        self.title_entry = ttk.Entry(add_card, font=("Segoe UI", 11))
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.title_entry.insert(0, "")
        self.title_entry.bind("<Return>", lambda _event: self.add_task())

        priority_box = ttk.Combobox(
            add_card,
            textvariable=self.priority_var,
            values=list(db.VALID_PRIORITIES),
            width=9,
            state="readonly",
        )
        priority_box.pack(side="left", padx=(0, 8))

        ttk.Button(add_card, text="Add", command=self.add_task, width=8).pack(side="left")

        # Filters
        filters = ttk.Frame(root, style="App.TFrame")
        filters.pack(fill="x", pady=(0, 8))
        for value, label in (
            ("active", "Active"),
            ("completed", "Done"),
            ("all", "All"),
        ):
            ttk.Radiobutton(
                filters,
                text=label,
                value=value,
                variable=self.filter_var,
                command=self.refresh_tasks,
            ).pack(side="left", padx=(0, 10))

        ttk.Button(filters, text="Delete done", command=self.clear_completed).pack(
            side="right"
        )

        # Scrollable task list
        list_wrap = ttk.Frame(root, style="Card.TFrame", padding=4)
        list_wrap.pack(fill="both", expand=True)

        canvas = tk.Canvas(list_wrap, bg="#ffffff", highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(list_wrap, orient="vertical", command=canvas.yview)
        self.tasks_frame = ttk.Frame(canvas, style="Card.TFrame")

        self.tasks_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        self._canvas_window = canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _resize_inner(event: tk.Event) -> None:
            canvas.itemconfigure(self._canvas_window, width=event.width)

        canvas.bind("<Configure>", _resize_inner)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas = canvas

        # Mouse wheel support (Windows)
        self.bind_all("<MouseWheel>", self._on_mousewheel)

        footer = ttk.Frame(root, style="App.TFrame")
        footer.pack(fill="x", pady=(10, 0))
        ttk.Label(
            footer,
            text="Tip: check a task to mark it complete. Same data as the CLI app.",
            style="Stats.TLabel",
        ).pack(anchor="w")

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def add_task(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Empty task", "Please enter a task title.")
            return
        if len(title) > 200:
            messagebox.showwarning("Too long", "Title must be at most 200 characters.")
            return

        db.add_task(
            title=title,
            description=None,
            priority=self.priority_var.get(),
            due_date=None,
            status="Pending",
        )
        self.title_entry.delete(0, tk.END)
        self.filter_var.set("active")
        self.refresh_tasks()

    def toggle_task(self, task_id: int) -> None:
        checked = self._check_vars[task_id].get()
        new_status = "Completed" if checked else "Pending"
        db.update_task(task_id, {"status": new_status})
        # Small delay feel: refresh to move item between filters
        self.refresh_tasks()

    def delete_task(self, task_id: int) -> None:
        task = db.get_task_by_id(task_id)
        if task is None:
            self.refresh_tasks()
            return
        if not messagebox.askyesno("Delete task", f'Delete "{task["title"]}"?'):
            return
        db.delete_task(task_id)
        self.refresh_tasks()

    def clear_completed(self) -> None:
        completed = db.filter_tasks(status="Completed")
        if not completed:
            messagebox.showinfo("Nothing to delete", "There are no completed tasks.")
            return
        if not messagebox.askyesno(
            "Delete done",
            f"Delete {len(completed)} completed task(s)?",
        ):
            return
        for task in completed:
            db.delete_task(task["id"])
        self.refresh_tasks()

    def refresh_tasks(self) -> None:
        for child in self.tasks_frame.winfo_children():
            child.destroy()
        self._check_vars.clear()

        mode = self.filter_var.get()
        if mode == "active":
            tasks = [
                t
                for t in db.get_all_tasks()
                if t["status"] in ("Pending", "In Progress")
            ]
        elif mode == "completed":
            tasks = db.filter_tasks(status="Completed")
        else:
            tasks = db.get_all_tasks()

        stats = db.get_statistics()
        active_count = stats["pending"] + stats["in_progress"]
        self.stats_label.configure(
            text=(
                f"{active_count} active · {stats['completed']} done · "
                f"{stats['completion_percentage']}% complete"
            )
        )

        if not tasks:
            empty = ttk.Label(
                self.tasks_frame,
                text="No tasks here yet.",
                style="Meta.TLabel",
                padding=16,
            )
            empty.pack(anchor="w")
            return

        for task in tasks:
            self._render_task_row(task)

    def _render_task_row(self, task) -> None:
        row = ttk.Frame(self.tasks_frame, style="Card.TFrame", padding=(10, 8))
        row.pack(fill="x", pady=2)

        done = task["status"] == "Completed"
        var = tk.BooleanVar(value=done)
        self._check_vars[task["id"]] = var

        check = ttk.Checkbutton(
            row,
            variable=var,
            style="Task.TCheckbutton",
            command=lambda task_id=task["id"]: self.toggle_task(task_id),
        )
        check.pack(side="left", padx=(0, 8))

        text_frame = ttk.Frame(row, style="Card.TFrame")
        text_frame.pack(side="left", fill="x", expand=True)

        title_color = "#9aa0a6" if done else "#202124"
        title_font = ("Segoe UI", 11, "overstrike") if done else ("Segoe UI", 11)
        title = tk.Label(
            text_frame,
            text=task["title"],
            bg="#ffffff",
            fg=title_color,
            font=title_font,
            anchor="w",
            justify="left",
            wraplength=360,
        )
        title.pack(fill="x", anchor="w")

        meta_bits = [task["priority"]]
        if task["due_date"]:
            meta_bits.append(f"due {task['due_date']}")
        if task["status"] == "In Progress":
            meta_bits.append("in progress")
        meta = ttk.Label(text_frame, text=" · ".join(meta_bits), style="Meta.TLabel")
        meta.pack(anchor="w")

        delete_btn = ttk.Button(
            row,
            text="✕",
            width=3,
            command=lambda task_id=task["id"]: self.delete_task(task_id),
        )
        delete_btn.pack(side="right", padx=(8, 0))


def main() -> None:
    app = TodoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
