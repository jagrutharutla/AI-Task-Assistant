from datetime import datetime

def prioritize_tasks(tasks):
    def score(task):
        # Convert deadline to date object or assign far future if missing
        deadline = task['deadline']
        if deadline:
            try:
                deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
            except ValueError:
                deadline_date = datetime.max
        else:
            deadline_date = datetime.max

        # Base score: closer deadline = higher priority
        days_left = (deadline_date - datetime.now()).days
        deadline_score = max(0, 30 - days_left)

        # Task type weighting
        type_score = 10 if task['type'] == 'Work' else 0

        return deadline_score + type_score

    # Filter out completed tasks
    incomplete = [t for t in tasks if t['completed'] == 0]
    return sorted(incomplete, key=score, reverse=True)