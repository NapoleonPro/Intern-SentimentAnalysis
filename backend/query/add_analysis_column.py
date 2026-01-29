import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

def migrate_db():
    print("Connecting to the database...")
    try:
        engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
        
        with engine.connect() as conn:
            print("Connection successful. Checking for 'analysis_method' column...")
            
            check_query = text("""
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='articles' AND column_name='analysis_method'
            """)
            result = conn.execute(check_query).fetchone()
            
            if result:
                print("Column 'analysis_method' already exists. No action needed.")
            else:
                print("Column not found. Adding 'analysis_method' to 'articles' table...")
                alter_query = text("ALTER TABLE articles ADD COLUMN analysis_method VARCHAR(50)")
                
                conn.execute(alter_query)
                conn.commit()
                print("Successfully added the 'analysis_method' column.")
                
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure the database is running and the connection details (DB_USER, DB_PASS, DB_NAME) are correct.")
if __name__ == "__main__":
    migrate_db()