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
        # First, let's count how many articles will be deleted
        count_query = text("SELECT COUNT(*) FROM articles WHERE EXTRACT(YEAR FROM published_date) = 2026")
        count_result = conn.execute(count_query).scalar_one()
        
        if count_result > 0:
            print(f"Ditemukan {count_result} artikel dari tahun 2026 yang akan dihapus.")
            
            # Proceed with deletion
            delete_query = text("DELETE FROM articles WHERE EXTRACT(YEAR FROM published_date) = 2026")
            result = conn.execute(delete_query)
            conn.commit()
            
            print(f"Berhasil! {result.rowcount} artikel dari tahun 2026 telah dihapus dari database.")
        else:
            print("Tidak ada artikel dari tahun 2026 yang ditemukan di database.")
            
    except Exception as e:
        print(f"Terjadi error saat mencoba menghapus data: {e}")
