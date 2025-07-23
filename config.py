import os 

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'devkey'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your-openai-api-key'
    DATABASE = 'tasks.db'