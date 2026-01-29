from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE articles ADD COLUMN sentiment_score FLOAT"))
        conn.commit()
        print("Fixed. Column 'sentiment_score' added.")
    except Exception as e:
        print(f"Info/Error: {e}")