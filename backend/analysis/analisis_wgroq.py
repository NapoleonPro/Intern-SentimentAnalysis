import os
from groq import Groq
from sqlalchemy import create_engine, text
import time
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

# --- KONFIGURASI ---
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# --- API KEY GROQ ---
# Masukkan key dari console.groq.com di sini
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

client = Groq(api_key=GROQ_API_KEY)
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def get_sentiment_batch(berita_list):
    """
    Mengirim 5 berita sekaligus ke Llama-3 via Groq.
    """
    # Prompt System: Memberi peran
    system_prompt = "Kamu adalah ahli analisis sentimen berita politik Aceh. Keluarkan hasil analisis dalam format JSON murni."
    
    # Merakit User Prompt
    user_content = "Analisis sentimen berita berikut menjadi: POS (Positif), NEG (Negatif), atau NEUT (Netral).\n\n"
    
    for i, (b_id, content) in enumerate(berita_list):
        # Llama-3 punya context window besar, aman 500 karakter
        snippet = content[:500].replace("\n", " ").replace('"', "'")
        user_content += f"ID_{b_id}: \"{snippet}...\"\n"
    
    user_content += """
    \nOUTPUT WAJIB JSON ARRAY (tanpa markdown ```json). 
    Contoh: [{"id": 101, "sentiment": "POS"}, {"id": 102, "sentiment": "NEG"}]
    Pastikan SEMUA ID di atas teranalisis.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Model Meta Llama 3 (Cepat & Pintar)
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0, # Supaya jawaban konsisten/tidak kreatif
            response_format={"type": "json_object"} # Fitur spesial Groq biar output pasti JSON
        )
        
        # Ambil jawaban
        raw_json = completion.choices[0].message.content
        
        # Parse JSON
        parsed = json.loads(raw_json)
        
        # Kadang Llama membungkus dalam key "berita" atau "data", kita cari list-nya
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            # Ambil value pertama yang berbentuk list
            for key, val in parsed.items():
                if isinstance(val, list):
                    return val
            # Kalau tidak ada list, mungkin cuma 1 item dict, bungkus jadi list
            return [parsed]
            
        return []

    except Exception as e:
        print(f"   ⚠️ Error Groq: {e}")
        return []

def run_analysis():
    BATCH_SIZE = 5       # Groq kuat 5-10 berita sekali jalan
    SLEEP_TIME = 2       # Groq sangat cepat, istirahat 2 detik cukup
    
    # Ambil SEMUA data (Re-Analysis 495 berita)
    with engine.connect() as conn:
        articles = conn.execute(text("""
            SELECT id, content 
            FROM articles 
            WHERE content IS NOT NULL 
            ORDER BY id DESC 
        """)).fetchall()
    
    print(f"🚀 Memulai Re-Analysis dengan Groq (Llama-3) untuk {len(articles)} berita...")
    
    chunks = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    total_updated = 0
    
    for i, chunk in enumerate(chunks):
        data_to_send = [(row.id, row.content) for row in chunk]
        
        print(f"[{i+1}/{len(chunks)}] Batch {len(data_to_send)} item...", end=" ")
        
        results = get_sentiment_batch(data_to_send)
        
        if results:
            with engine.connect() as conn:
                for res in results:
                    try:
                        # Bersihkan ID, validasi & mapping label
                        raw_id = str(res.get('id', '')).replace('ID_', '')
                        clean_id = int(re.sub(r'\D', '', raw_id))
                        
                        label_map = {'POS': 'Positif', 'NEG': 'Negatif', 'NEUT': 'Netral'}
                        raw_label = res.get('sentiment', 'NEUT').upper()
                        if raw_label not in label_map: raw_label = 'NEUT'
                        final_label = label_map[raw_label]
                        
                        conn.execute(
                            text("UPDATE articles SET sentiment_label = :s, analysis_method = 'Llama3-70B-Groq', updated_at = NOW() WHERE id = :id"),
                            {"s": final_label, "id": clean_id}
                        )
                    except Exception as sub_e:
                        pass # Skip jika ada 1 item error parsing
            print(f"✅ Ok ({len(results)} saved)")
            total_updated += len(results)
        else:
            print("❌ Gagal")

        # Jeda sebentar
        time.sleep(SLEEP_TIME)

    print(f"🏁 Selesai! Total {total_updated} berita berhasil diupdate.")

if __name__ == "__main__":
    run_analysis()