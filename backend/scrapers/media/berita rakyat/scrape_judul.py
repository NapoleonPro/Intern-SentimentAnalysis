import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from datetime import datetime
import time
import random
DB_USER = 'postgres'
DB_PASS = 'admin'
DB_NAME = 'db_pkp_aceh'
DB_HOST = 'localhost'
DB_PORT = '5432'
SEARCH_QUERY = "pemerintah+aceh"
BASE_URL = "https://beritarakyataceh.com"
MUST_HAVE_KEYWORDS = ["pemerintah aceh", "pemprov aceh", "gubernur aceh", "wagub aceh", "sekda aceh", "dpra"]
CUTOFF_DAYS = 90
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
def is_relevant(title):
    title_lower = title.lower()
    for kw in MUST_HAVE_KEYWORDS:
        if kw in title_lower:
            return True
    return False
def check_date(date_str):
    if not date_str: return 2
    try:
        article_date = datetime.fromisoformat(date_str)
        now = datetime.now(article_date.tzinfo)
        delta = now - article_date
        
        if delta.days <= CUTOFF_DAYS:
            return 0
        else:
            return 1
    except:
        return 2
def save_to_db(title, url, date_str):
    try:
        with engine.connect() as conn:
            check = conn.execute(text("SELECT id FROM articles WHERE url = :u"), {"u": url}).fetchone()
            if check: return "DUPLICATE"
            query = text("""
                INSERT INTO articles (title, url, published_date, source, created_at)
                VALUES (:t, :u, :d, 'beritarakyataceh.com', NOW())
            """)
            conn.execute(query, {"t": title, "u": url, "d": date_str})
            conn.commit()
            return "SAVED"
    except Exception as e:
        print(f"   [Error DB] {e}")
        return "ERROR"
def run_scraper():
    page = 1
    total_saved = 0
    keep_going = True
    
    print(f" Memulai Scrape Pintar (Skip Mode): {BASE_URL}")
    print(f"   Target: 3 Bulan Terakhir ({CUTOFF_DAYS} hari)")
    print("-" * 60)
    while keep_going:
        if page == 1:
            url = f"{BASE_URL}/?s={SEARCH_QUERY}"
        else:
            url = f"{BASE_URL}/page/{page}/?s={SEARCH_QUERY}"
            
        print(f"\n Membuka Halaman {page}...")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 404:
                print("    Halaman Habis. Selesai.")
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            articles = soup.select('article.item-content')
            
            if not articles:
                print("    Tidak ada artikel. Selesai.")
                break
            
            old_articles_on_page = 0
            
            for item in articles:
                title_tag = item.select_one('h2.entry-title a')
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                link = title_tag['href']
                
                time_tag = item.select_one('time.entry-date')
                pub_date = time_tag['datetime'] if time_tag else None
                
                date_status = check_date(pub_date)
                
                if date_status == 1:
                    old_articles_on_page += 1
                    continue
                
                if not is_relevant(title):
                    continue
                status = save_to_db(title, link, pub_date)
                if status == "SAVED":
                    print(f"    [{pub_date[:10]}] {title[:40]}...")
                    total_saved += 1
            if old_articles_on_page == len(articles):
                print(f"    Seluruh halaman {page} berisi berita lama. Stop Scraping.")
                keep_going = False
                break
            
            page += 1
            time.sleep(1)
            
        except Exception as e:
            print(f" Error Halaman {page}: {e}")
            break
    print("-" * 60)
    print(f" Selesai! Total berita baru tersimpan: {total_saved}")
if __name__ == "__main__":
    run_scraper()