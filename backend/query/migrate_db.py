import os
from sqlalchemy import create_engine, text
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'admin')
DB_NAME = os.getenv('DB_NAME', 'db_pkp_aceh')
def migrate_db():
    print("Connecting to the database...")
    try:
        engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}')
        
        with engine.connect() as conn:
            print("Connection successful. Checking schema...")
            
            check_updated_at = text("SELECT 1 FROM information_schema.columns WHERE table_name='articles' AND column_name='updated_at'")
            if not conn.execute(check_updated_at).fetchone():
                print("Column 'updated_at' not found. Adding it...")
                alter_updated_at = text("ALTER TABLE articles ADD COLUMN updated_at TIMESTAMPTZ")
                conn.execute(alter_updated_at)
                print("Successfully added 'updated_at'.")
            else:
                print("Column 'updated_at' already exists.")
            check_notes = text("SELECT 1 FROM information_schema.columns WHERE table_name='articles' AND column_name='analysis_notes'")
            if not conn.execute(check_notes).fetchone():
                print("Column 'analysis_notes' not found. Adding it...")
                alter_notes = text("ALTER TABLE articles ADD COLUMN analysis_notes TEXT")
                conn.execute(alter_notes)
                print("Successfully added 'analysis_notes'.")
            else:
                print("Column 'analysis_notes' already exists.")
            conn.commit()
            print("\nDatabase schema check complete.")
                
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure the database is running and the connection details are correct.")
if __name__ == "__main__":
    migrate_db()