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
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}')
def get_empty_articles():
    with engine.connect() as conn:
        query = text("SELECT id, url, title FROM articles WHERE content IS NULL ORDER BY id DESC")
        result = conn.execute(query)
        return result.fetchall()
def update_content(article_id, content_text):
    with engine.connect() as conn:
        query = text("UPDATE articles SET content = :content WHERE id = :id")
        conn.execute(query, {"content": content_text, "id": article_id})
        conn.commit()
def scrape_body():
    articles = get_empty_articles()
    total = len(articles)
    
    print(f"Memulai Content Scraping. Ada {total} artikel antri untuk diproses.")
    print("-" * 50)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for index, row in enumerate(articles):
        id_berita = row[0]
        url = row[1]
        judul = row[2]
        print(f"[{index+1}/{total}] Sedang menyedot: {judul[:40]}...")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Gagal akses URL (Status: {response.status_code})")
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            content_div = soup.find('div', id='single-article-text')
            if not content_div:
                content_div = soup.find('div', class_='single-article-text')
            if content_div:
                paragraphs = content_div.find_all('p')
                full_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
                
                if "Baca Juga" in full_text:
                    full_text = full_text.split("Baca Juga")[0]
                if len(full_text) > 50:
                    update_content(id_berita, full_text)
                    print(f"Berhasil! Panjang teks: {len(full_text)} karakter.")
                else:
                    print("Teks terlalu pendek, mungkin gagal scrape.")
            else:
                print("Gagal menemukan ID 'single-article-text'. Struktur beda?")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(random.uniform(2, 4))
    print("-" * 50)
    print("Selesai! Semua konten sudah tersimpan di Database.")
if __name__ == "__main__":
    scrape_body()