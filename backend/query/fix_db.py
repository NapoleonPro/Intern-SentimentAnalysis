from sqlalchemy import create_engine, text
DB_USER = 'postgres'
DB_PASS = 'admin'
DB_NAME = 'db_pkp_aceh'
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}')
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE articles ADD COLUMN sentiment_score FLOAT"))
        conn.commit()
        print("Fixed. Column 'sentiment_score' added.")
    except Exception as e:
        print(f"Info/Error: {e}")