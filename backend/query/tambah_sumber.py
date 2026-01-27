from sqlalchemy import create_engine, text
DB_USER = 'postgres'
DB_PASS = 'admin'
DB_NAME = 'db_pkp_aceh'
DB_HOST = 'localhost'
DB_PORT = '5432'
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