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
def fix_table():
    print(" Menambahkan kolom 'source'...")
    
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE articles ADD COLUMN IF NOT EXISTS source VARCHAR(100);"))
            
            conn.execute(text("UPDATE articles SET source = 'noa.co.id' WHERE source IS NULL;"))
            
            conn.commit()
            print(" Berhasil! Kolom source sudah ditambahkan.")
            
        except Exception as e:
            print(f" Error: {e}")
if __name__ == "__main__":
    fix_table()