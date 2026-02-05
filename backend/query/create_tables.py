import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

if not all([DB_USER, DB_PASS, DB_NAME, DB_HOST, DB_PORT]):
    print("Error: Database environment variables are not set.")
    print("Please check your backend/.env file.")
    exit(1)

CREATE_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

def create_tables():

    try:
        engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
        with engine.connect() as conn:
            print("Connecting to the database...")
            conn.execute(text(CREATE_USERS_TABLE_SQL))
            conn.commit()
            print("✅ Table 'users' created successfully (if it didn't exist).")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    print("--- Database Table Creation Script ---")
    confirm = input("This will create the 'users' table in the database. Continue? (y/n): ").lower()
    if confirm == 'y':
        create_tables()
    else:
        print("Operation cancelled.")
