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
CONTENT_SELECTORS = [
    {'id': 'single-article-text'}, 
    
    {'class_': 'entry-content'},
    
    {'class_': 'post-content'},
    {'class_': 'article-content'},
    {'class_': 'detail-text'},
    {'tag': 'article'}
]
def get_unscraped_articles():
    with engine.connect() as conn:
        query = text("SELECT id, url, title FROM articles WHERE content IS NULL ORDER BY created_at DESC LIMIT 10")
        return conn.execute(query).fetchall()
def update_content(article_id, content_text):
    with engine.connect() as conn:
        query = text("UPDATE articles SET content = :c WHERE id = :id")
        conn.execute(query, {"c": content_text, "id": article_id})
        conn.commit()
def fetch_body(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for script in soup(["script", "style", "iframe", "noscript"]):
            script.decompose()
        found_text = ""
        
        for selector in CONTENT_SELECTORS:
            element = None
            
            if 'id' in selector:
                element = soup.find(id=selector['id'])
            elif 'class_' in selector:
                element = soup.find(class_=selector['class_'])
            elif 'tag' in selector:
                element = soup.find(selector['tag'])
            
            if element:
                paragraphs = element.find_all('p')
                if paragraphs:
                    found_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
                else:
                    found_text = element.get_text(strip=True)
                
                if len(found_text) > 50:
                    print(f"   [INFO] Selector tembus pakai: {selector}")
                    break
        if not found_text:
            return "[GAGAL] Konten tidak ditemukan dengan selector manapun."
        return found_text
    except Exception as e:
        return f"[ERROR] Network: {e}"
def scrape_body():
    tasks = get_unscraped_articles()
    
    if not tasks:
        print(" Semua berita sudah discrape. Tidak ada antrian.")
        return
    print(f"Memulai Content Scraping Universal. Ada {len(tasks)} artikel antri.")
    print("-" * 60)
    for i, row in enumerate(tasks):
        a_id, url, title = row
        print(f"[{i+1}/{len(tasks)}] Menyedot: {title[:40]}...")
        
        content = fetch_body(url)
        
        if content and "[ERROR]" not in content and "[GAGAL]" not in content:
            update_content(a_id, content)
            print("    Berhasil disimpan.")
        else:
            print(f"    Gagal: {content[:50]}...")
            
        time.sleep(random.uniform(1, 3))
    print("-" * 60)
    print("Selesai.")
if __name__ == "__main__":
    scrape_body()