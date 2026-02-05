from huggingface_hub import InferenceClient
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

HF_TOKEN = os.getenv('HUGGINGFACE_API_KEY') # 



MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

client = InferenceClient(api_key=HF_TOKEN)
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def get_sentiment_batch(berita_list):

    system_prompt = "Kamu adalah ahli analisis sentimen berita politik Aceh. Tugasmu hanya satu: Keluarkan hasil klasifikasi dalam format JSON murni."
    
    user_content = "Analisis sentimen berita berikut menjadi salah satu dari: POS (Positif), NEG (Negatif), atau NEUT (Netral).\n\n"
    
    for i, (b_id, content) in enumerate(berita_list):

        snippet = content[:400].replace("\n", " ").replace('"', "'")
        user_content += f"ID_{b_id}: \"{snippet}...\"\n"
    
    user_content += """
    \nOUTPUT WAJIB JSON ARRAY MURNI (tanpa markdown).
    Contoh: [{"id": 101, "sentiment": "POS"}, {"id": 102, "sentiment": "NEG"}]
    Pastikan semua ID terjawab.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    try:
        response = client.chat_completion(
            model=MODEL_ID,
            messages=messages,
            max_tokens=500,  
            temperature=0.1  
        )
        
        raw_json = response.choices[0].message.content
        
        clean_json = re.sub(r"```json|```", "", raw_json).strip()
        
        parsed = json.loads(clean_json)
        
        
        if isinstance(parsed, list): return parsed
        elif isinstance(parsed, dict): return [parsed]
        return []

    except Exception as e:
        error_msg = str(e)
        
        
        if "503" in error_msg or "429" in error_msg or "Loading" in error_msg:
            return "SERVER_BUSY"
        
        print(f" Error HF: {e}")
        return []

def run_analysis():
    BATCH_SIZE = 3       
    SLEEP_TIME = 2       
    
    print("🔄 Mengambil SEMUA data berita dari database...")
    
    
    with engine.connect() as conn:
        articles = conn.execute(text("""
            SELECT id, content 
            FROM articles 
            WHERE content IS NOT NULL 
            ORDER BY id DESC 
        """)).fetchall()
    
    if not articles:
        print(" Tidak ada berita untuk diproses.")
        return

    print(f"🚀 Memulai Re-Analysis Total via Hugging Face ({len(articles)} berita)...")
    print("   (Model: Qwen-2.5-72B - Gratis tapi mungkin perlu retry jika server sibuk)")
    
    chunks = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    total_updated = 0
    
    for i, chunk in enumerate(chunks):
        data_to_send = [(row.id, row.content) for row in chunk]
        
        print(f"[{i+1}/{len(chunks)}] Batch {len(data_to_send)} item...", end=" ")
        
    
        while True: 
            results = get_sentiment_batch(data_to_send)
            
            if results == "SERVER_BUSY":
                print("\n   ⏳ Server HF sibuk/loading. Tunggu 10 detik...", end=" ")
                time.sleep(10)
                continue 
            
            break 
        
        if results:
            with engine.connect() as conn:
                for res in results:
                    try:
                        raw_id = str(res.get('id', '')).replace('ID_', '')
                        clean_id = int(re.sub(r'\D', '', raw_id))
                        
                        label_map = {'POS': 'Positif', 'NEG': 'Negatif', 'NEUT': 'Netral'}
                        raw_label = res.get('sentiment', 'NEUT').upper()
                        if raw_label not in label_map: raw_label = 'NEUT'
                        final_label = label_map[raw_label]
                        
                        
                        conn.execute(
                            text("UPDATE articles SET sentiment_label = :s, analysis_method = 'Qwen/72B-Instruct', updated_at = NOW() WHERE id = :id"),
                            {"s": final_label, "id": clean_id}
                        )
                        conn.commit()
                    except: pass
            print(f"✅ Ok ({len(results)} saved)")
            total_updated += len(results)
        else:
            print("Gagal parsing/API Error")

        time.sleep(SLEEP_TIME)

    print(f"Selesai Bos! Total {total_updated} berita berhasil di-update.")