from flask import Blueprint, render_template, request, redirect, url_for
from .db import get_db
from .logic import prioritize_tasks
#from .ai import query_assistant
from .ai import query_assistant_agent

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
    deadline = request.form.get('deadline')  # Optional
    task_type = request.form.get('type')     # Optional

    db = get_db()
    db.execute(
        'INSERT INTO tasks (description, deadline, type) VALUES (?, ?, ?)',
        (description, deadline, task_type)
    )
    db.commit()
    return redirect(url_for('main.index'))

#@main.route('/ask', methods=['POST'])
#def ask():
#    user_input = request.form['query']
#    db = get_db()
#    tasks = db.execute('SELECT * FROM tasks').fetchall()
#    response = query_assistant(tasks, user_input)
#   return render_template('index.html', tasks=tasks, answer=response)

@main.route('/agent', methods=['POST'])
def agent():
    user_input = request.form['query']
    db = get_db()
    tasks = db.execute('SELECT * FROM tasks').fetchall()
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
    elif intent == "delete":
        db.execute(
            "DELETE FROM tasks WHERE LOWER(description) LIKE LOWER(?)",
            (f"%{args.get('description', '')}%",)
        )
    elif intent == "query":
        query_type = args.get("query_type", "").lower()

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

        elif "completed_tasks_count" in query_type or "completed" in query_type:
            stats = db.execute("""
                SELECT COUNT(*) as total,
                    SUM(completed = 1) as completed
                FROM tasks
            """).fetchone()
            total = stats["total"] or 0
            done = stats["completed"] or 0
            pct = (done / total * 100) if total > 0 else 0
            message = f"You've completed {done} out of {total} tasks ({pct:.1f}%)."

        else:
            message = "Sorry, I couldn't analyze that type of query yet."

    db.commit()

    # Show updated task list
    updated_tasks = db.execute('SELECT * FROM tasks').fetchall()
    prioritized = prioritize_tasks(updated_tasks)
    return render_template("index.html", tasks=prioritized, answer=message)