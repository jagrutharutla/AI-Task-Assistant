# 🧠 Personal AI Task Assistant

A lightweight, AI-powered personal assistant that helps you manage and prioritize your daily tasks using natural language and contextual awareness.

Built with:
- Python + Flask (Backend)
- SQLite (Storage)
- OpenAI GPT API (AI Agent)
- Rule-based + AI-driven task logic
- Simple HTML/CSS frontend

---

## 🚀 Features

✅ Add, complete, or delete tasks using natural language  
✅ Prioritize tasks based on deadline, type, and past behavior  
✅ Ask introspective queries like:  
   > “What do I usually delay?”  
   > “How many work tasks have I completed?”  
✅ Minimal UI with AI agent-first interaction  
✅ Local persistent memory via SQLite  

---

## 🛠️ Tech Stack

- Python 3.9+
- Flask
- SQLite
- OpenAI GPT (v1.x client)
- HTML/CSS (optional enhancements welcome)

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-task-assistant.git
cd ai-task-assistant

2. Set up a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3. Install dependencies

pip install flask openai

4. Set up environment variables
Create a .env file or export directly:
export OPENAI_API_KEY=your-openai-api-key

On Windows (CMD):
set OPENAI_API_KEY=your-openai-api-key

🗃️ Database Setup
1. Initialize the SQLite database
Make sure schema.sql exists in the root directory.

Then run:
flask --app main.py init-db
This will create tasks.db and set up the tasks table.

▶️ Running the App
python main.py
