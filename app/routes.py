from flask import Blueprint, render_template, request, redirect, url_for
import pickle
import sqlite3
from .db import get_db
from .logic import prioritize_tasks
from .ai import query_assistant_agent, get_embedding, find_similar_past_tasks

main = Blueprint('main', __name__)


@main.route('/')
def index():
    db = get_db()
    tasks = db.execute('SELECT * FROM tasks ORDER BY deadline').fetchall()
    prioritized = prioritize_tasks(tasks)
    return render_template('index.html', tasks=prioritized)


@main.route('/add', methods=['POST'])
def add_task():
    description = request.form['description']
    deadline = request.form.get('deadline')
    task_type = request.form.get('type')

    db = get_db()
    db.execute(
        'INSERT INTO tasks (description, deadline, type) VALUES (?, ?, ?)',
        (description, deadline, task_type)
    )
    db.commit()
    return redirect(url_for('main.index'))


@main.route('/agent', methods=['POST'])
def agent():
    user_input = request.form['query']
    db = get_db()
    tasks = db.execute('SELECT * FROM tasks ORDER BY deadline').fetchall()

    result = query_assistant_agent(tasks, user_input)
    intent = result.get("intent")
    args = result.get("arguments", {})
    message = result.get("response", "OK")

    if intent == "add":
        db.execute(
            'INSERT INTO tasks (description, deadline, type) VALUES (?, ?, ?)',
            (args.get("description"), args.get("deadline"), args.get("type"))
        )

    elif intent == "complete":
        db.execute(
            "UPDATE tasks SET completed = 1 WHERE LOWER(description) LIKE LOWER(?)",
            (f"%{args.get('description', '')}%",)
        )

        completed_task = db.execute(
            "SELECT id, description FROM tasks WHERE LOWER(description) LIKE LOWER(?)",
            (f"%{args.get('description', '')}%",)
        ).fetchone()

        if completed_task:
            emb = get_embedding(completed_task["description"])
            db.execute("""
                INSERT INTO memory (task_id, content, embedding)
                VALUES (?, ?, ?)
            """, (completed_task["id"], completed_task["description"], sqlite3.Binary(pickle.dumps(emb))))

    elif intent == "delete":
        db.execute(
            "DELETE FROM tasks WHERE LOWER(description) LIKE LOWER(?)",
            (f"%{args.get('description', '')}%",)
        )

    elif intent == "query":
        query_type = args.get("query_type", "").lower().replace("_", " ").strip()

        if not query_type and any(word in user_input.lower() for word in ["recall", "past", "completed"]):
            query_type = "recall"

        if "work" in query_type:
            stats = db.execute("""
                SELECT COUNT(*) as total,
                       SUM(completed = 1) as completed
                FROM tasks
                WHERE type = 'Work'
            """).fetchone()
            total = stats["total"] or 0
            done = stats["completed"] or 0
            message = f"You had {total} work tasks. {done} of them were completed."

        elif "personal" in query_type:
            stats = db.execute("""
                SELECT COUNT(*) as total,
                       SUM(completed = 1) as completed
                FROM tasks
                WHERE type = 'Personal'
            """).fetchone()
            total = stats["total"] or 0
            done = stats["completed"] or 0
            message = f"You had {total} personal tasks. {done} completed, {total - done} left."

        elif "completed tasks" in query_type or "completion rate" in query_type or "completed" in query_type:
            stats = db.execute("""
                SELECT COUNT(*) as total,
                       SUM(completed = 1) as completed
                FROM tasks
            """).fetchone()
            total = stats["total"] or 0
            done = stats["completed"] or 0
            pct = (done / total * 100) if total > 0 else 0
            message = f"You've completed {done} out of {total} tasks ({pct:.1f}%)."

        elif args.get("description"):
                matches = find_similar_past_tasks(args["description"])
                if matches:
                    message = "Here are similar things you've done before:<ul>"
                    for m in matches:
                        message += f"<li>{m}</li>"
                    message += "</ul>"
                else:
                    message = "I couldn't find anything similar in your completed tasks."

        else:
            message = "Sorry, I couldn't analyze that type of query yet."

    db.commit()

    updated_tasks = db.execute('SELECT * FROM tasks ORDER BY deadline').fetchall()
    prioritized = prioritize_tasks(updated_tasks)
    return render_template("index.html", tasks=prioritized, answer=message)
