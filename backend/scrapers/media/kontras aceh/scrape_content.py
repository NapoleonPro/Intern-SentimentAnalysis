import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
import time
import random
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS") 
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def get_unscraped_kontras():
    with engine.connect() as conn:
        query = text("""
            SELECT id, url, title 
            FROM articles 
            WHERE source = 'kontrasaceh.net' 
            AND content IS NULL 
            ORDER BY created_at DESC
        """)
        return conn.execute(query).fetchall()

def update_content(article_id, content_text):
    with engine.connect() as conn:
        query = text("UPDATE articles SET content = :c WHERE id = :id")
        conn.execute(query, {"c": content_text, "id": article_id})
        conn.commit()

def fetch_body(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Target Khusus Tema JNews: .content-inner
        container = soup.select_one('.content-inner')
        
        # Jika gagal, coba fallback ke .entry-content (standar WordPress)
        if not container:
            container = soup.select_one('.entry-content')

        if not container:
            return "[GAGAL] Konten tidak ditemukan."

        for tag in container.select('.jeg_ad, script, style, .ads-wrapper'):
            tag.decompose()

        paragraphs = container.find_all('p')
        text_content = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        if not text_content: return "[GAGAL] Teks kosong."
        
        return text_content

    except Exception as e:
        return f"[ERROR] {e}"

def run():
    tasks = get_unscraped_kontras()
    print(f"🚀 Memproses {len(tasks)} antrian Kontras Aceh...")
    
    for i, row in enumerate(tasks):
        print(f"[{i+1}/{len(tasks)}] {row.title[:40]}...")
        content = fetch_body(row.url)
        
        if "GAGAL" not in content and "ERROR" not in content:
            update_content(row.id, content)
            print("   ✅ OK")
        else:
            print(f"   ❌ {content}")
        
        time.sleep(random.uniform(1, 2))

if __name__ == "__main__":
    run()