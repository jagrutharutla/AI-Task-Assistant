import openai
import json
import re
import dateparser
from datetime import datetime
from datetime import date
from flask import current_app
import numpy as np
import pickle
import sqlite3
from flask import current_app
from .db import get_db

client = openai.OpenAI()

def query_assistant_agent(tasks, user_input):
    today = date.today().isoformat()
    formatted_tasks = [
        {
            "id": t["id"],
            "description": t["description"],
            "deadline": t["deadline"],
            "type": t["type"],
            "completed": t["completed"]
        }
        for t in tasks
    ]

    recent_history = [
    {
        "description": t["description"],
        "deadline": t["deadline"],
        "type": t["type"],
        "completed": t["completed"],
        "created_at": t["created_at"]
    }
    for t in tasks if t["completed"] == 1
    ][-5:]  # Showing 5 most recent for brevity

    system_prompt = f"""
You are an intelligent task assistant. Your job is to interpret the user's natural language input and return a JSON response representing their intent.

ALWAYS format dates in YYYY-MM-DD. If the user says "tomorrow", "Friday", "in 3 days", etc., convert it to a real date. Today is {today}.

Return JSON with:
- intent: one of ["add", "complete", "delete", "query", "unknown"]
- arguments: dictionary with keys depending on the intent
- response: a short explanation

Example:
User: "Remind me to call mom next Thursday"
{{
  "intent": "add",
  "arguments": {{
    "description": "call mom",
    "deadline": "2025-07-24"
  }},
  "response": "Added 'call mom' for July 24."
}}


Now handle this:
Recent completed tasks:
{recent_history}

Tasks = {formatted_tasks}

User: "{user_input}"

Respond with JSON only.
""".strip()

    try:
        chat_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}],
            max_tokens=300,
            temperature=0.4,
        )

        reply = chat_response.choices[0].message.content.strip()

        # Debugging aid
        print("\nGPT raw reply:\n", reply)

        # Remove accidental markdown formatting
        if reply.startswith("```json"):
            reply = reply.replace("```json", "").strip()
        if reply.endswith("```"):
            reply = reply[:-3].strip()

        # Extract JSON block from GPT reply
        json_match = re.search(r'{.*}', reply, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            # 🔁 Convert deadline to actual date
            if parsed.get("intent") == "add":
                deadline = parsed["arguments"].get("deadline")
                if deadline:
                    parsed_date = dateparser.parse(deadline)
                    if parsed_date:
                        parsed["arguments"]["deadline"] = parsed_date.strftime('%Y-%m-%d')
            return parsed
        else:
            raise ValueError("No JSON object found")

    except Exception as e:
        print("Error parsing GPT response:", e)
        return {
            "intent": "unknown",
            "arguments": {},
            "response": "I'm sorry, I didn't understand that. Please try again."
        }
    
def get_embedding(text):
    client = openai.OpenAI()
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # or use another
    )
    return response.data[0].embedding

def find_similar_past_tasks(query, top_n=3):
    query_emb = get_embedding(query)
    db = get_db()

    rows = db.execute("SELECT id, content, embedding FROM memory").fetchall()
    scored = []

    for row in rows:
        emb = pickle.loads(row["embedding"])
        similarity = cosine_similarity(query_emb, emb)
        scored.append((similarity, row["content"]))

    # Sort by similarity, high to low
    scored.sort(reverse=True)
    return [text for _, text in scored[:top_n]]

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))