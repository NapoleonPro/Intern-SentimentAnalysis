import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
import time
import random
import os
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
def get_unscraped_hra():
    with engine.connect() as conn:
        query = text("""
            SELECT id, url, title 
            FROM articles 
            WHERE source = 'harianrakyataceh.com' 
            AND content IS NULL 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        return conn.execute(query).fetchall()
def update_content(article_id, content_text):
    with engine.connect() as conn:
        query = text("UPDATE articles SET content = :c WHERE id = :id")
        conn.execute(query, {"c": content_text, "id": article_id})
        conn.commit()
def scrape_hra_body(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        container = soup.select_one('.the-content')
        
        if not container:
            return "[GAGAL] Class '.the-content' tidak ditemukan."
        for ad in container.select('.funds'):
            ad.decompose()
            
        for related in container.select('.related-box'):
            related.decompose()
        for meta in container.select('.meta-info'):
            meta.decompose()
        for script in container(["script", "style", "iframe"]):
            script.decompose()
        paragraphs = container.find_all('p')
        text_content = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        if not text_content:
            return "[GAGAL] Teks kosong setelah pembersihan."
        return text_content
    except Exception as e:
        return f"[ERROR] {e}"
def run():
    while True:
        tasks = get_unscraped_hra()
        
        if not tasks:
            print(" Semua berita Harian Rakyat Aceh sudah discrape isinya.")
            break
        print(f" Memproses {len(tasks)} antrian HRA...")
        
        for row in tasks:
            a_id, url, title = row
            print(f"   - Menyedot: {title[:30]}...")
            
            content = scrape_hra_body(url)
            
            if "GAGAL" not in content and "ERROR" not in content:
                update_content(a_id, content)
                print("      OK")
            else:
                print(f"      {content}")
                
            time.sleep(random.uniform(1, 3))
if __name__ == "__main__":
    run()