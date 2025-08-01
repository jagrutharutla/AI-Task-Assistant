from datetime import datetime

def prioritize_tasks(tasks):
    from datetime import datetime

    def score(task):
        deadline = task['deadline']
        if deadline:
            try:
                due = datetime.strptime(deadline, "%Y-%m-%d")
                days_left = (due - datetime.now()).days
                deadline_score = max(0, 30 - days_left)
            except:
                deadline_score = 0
        else:
            deadline_score = 0

        type_score = 10 if task['type'] == 'Work' else 0
        return deadline_score + type_score

    return sorted(tasks, key=score, reverse=True)
