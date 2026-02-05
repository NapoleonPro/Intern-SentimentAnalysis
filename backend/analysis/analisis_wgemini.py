import google.generativeai as genai
from sqlalchemy import create_engine, text
import time
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()


DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS') 
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# API KEY (Pastikan nama variabel di .env file Anda adalah 'GEMINI_API_KEY')
GOOGLE_API_KEY = os.getenv('api')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def get_sentiment_batch(berita_list):

    
    prompt_text = "Tugasmu adalah analis sentimen berita Aceh. Nilai sentimen berita di bawah ini menjadi: POS (Positif), NEG (Negatif), atau NEUT (Netral).\n\n"
    
    for i, (b_id, content) in enumerate(berita_list):
        # Potong teks biar token gak meledak (cukup 300 karakter awal biasanya sudah ketahuan sentimennya)
        snippet = content[:300].replace("\n", " ") 
        prompt_text += f"Berita {i+1} (ID: {b_id}): \"{snippet}...\"\n"
    
    prompt_text += "\nJawab dengan format JSON murni dan valid: [{'id': ID, 'sentiment': 'LABEL'}, ...]"

    try:
        response = model.generate_content(prompt_text)
        raw_json = response.text.strip()
        
        # Bersihkan format markdown ```json ... ``` kalau ada
        raw_json = re.sub(r"```json|```", "", raw_json).strip()
        
        return json.loads(raw_json)
        
    except json.JSONDecodeError as e:
        print(f"   Error JSON Decode: {e}")
        print(f"   RAW Response: {raw_json}") # Tampilkan apa yang dikirim model
        return []
    except Exception as e:
        print(f"   Error Batch API: {e}")
        return []

def run_analysis():
    BATCH_SIZE = 5 # Kirim 5 berita per request
    
    # Ambil berita yg belum ada sentimen
    with engine.connect() as conn:
        articles = conn.execute(text("""
            SELECT id, content 
            FROM articles 
            WHERE sentiment IS NULL 
            AND content IS NOT NULL 
            ORDER BY created_at DESC
        """)).fetchall()
    
    if not articles:
        print("✅ Semua berita sudah dianalisis.")
        return

    print(f"Memulai Analisis Gemini (Mode Batch) untuk {len(articles)} artikel...")
    
    chunks = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    
    total_processed = 0
    
    for chunk in chunks:
        data_to_send = [(row.id, row.content) for row in chunk]
        
        print(f"   Memproses batch {len(data_to_send)} berita...", end=" ")
        
        results = get_sentiment_batch(data_to_send)
        
        if results:
            print(f"Dapat {len(results)} jawaban. Menyimpan ke DB...", end=" ")
            
            
            with engine.begin() as conn: 
                for res in results:
                    label_map = {'POS': 'Positif', 'NEG': 'Negatif', 'NEUT': 'Netral'}
                    raw_label = res.get('sentiment', 'NEUT').upper()
                    if raw_label not in label_map: raw_label = 'NEUT'
                    final_label = label_map[raw_label]
                    
                    conn.execute(
                            text("UPDATE articles SET sentiment_label = :s, analysis_method = 'Gemini-2.5-Flash', updated_at = NOW() WHERE id = :id"),
                            {"s": final_label, "id": res['id']}
                        )
            
            print("berhasil")
            total_processed += len(results)
        else:
            print(" Gagal")

        
        
        time.sleep(4) 

    print(f"Total berita dianalisis: {total_processed}")

