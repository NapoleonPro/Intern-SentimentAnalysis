import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from datetime import datetime
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
BASE_URL = "https://harianrakyataceh.com/search/?q=pemerintah+aceh"
MUST_HAVE_KEYWORDS = ["pemerintah", "pemprov", "gubernur", "wagub", "sekda", "aceh"]
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
def is_relevant(title):
    title_lower = title.lower()
    for kw in MUST_HAVE_KEYWORDS:
        if kw in title_lower:
            return True
    return False
def check_date_range(date_str):
    if not date_str: return 1
    
    try:
        dt = datetime.fromisoformat(date_str)
        
        start_date = datetime(2025, 10, 1, tzinfo=dt.tzinfo)
        end_date = datetime(2025, 12, 31, 23, 59, 59, tzinfo=dt.tzinfo)
        
        if dt > end_date:
            return 1
        elif start_date <= dt <= end_date:
            return 0
        else:
            return 2
            
    except Exception as e:
        print(f"   [Warn] Gagal parse tanggal: {e}")
        return 1
def save_to_db(title, url, date_str):
    try:
        with engine.connect() as conn:
            check = conn.execute(text("SELECT id FROM articles WHERE url = :u"), {"u": url}).fetchone()
            if check: return "DUPLICATE"
            query = text("""
                INSERT INTO articles (title, url, published_date, source, created_at)
                VALUES (:t, :u, :d, 'harianrakyataceh.com', NOW())
            """)
            conn.execute(query, {"t": title, "u": url, "d": date_str})
            conn.commit()
            return "SAVED"
    except Exception as e:
        print(f"   [Error DB] {e}")
        return "ERROR"
def run_scraper():
    current_url = BASE_URL
    total_saved = 0
    page_num = 1
    
    print(f" Memulai Scrape Harian Rakyat Aceh")
    print(f"   Target: 1 Oktober 2025 - 31 Desember 2025")
    print("-" * 60)
    while current_url:
        print(f"\n Memproses Halaman {page_num}...")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}
            resp = requests.get(current_url, headers=headers, timeout=15)
            
            if resp.status_code != 200:
                print("    Halaman tidak bisa dibuka. Berhenti.")
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            articles = soup.select('article')
            
            if not articles:
                print("    Tidak ada artikel ditemukan. Selesai.")
                break
                
            stop_signal = False
            
            for item in articles:
                title_tag = item.select_one('a.title')
                time_tag = item.select_one('time')
                
                if not title_tag or not time_tag:
                    continue
                    
                title = title_tag.get_text(strip=True)
                link = title_tag['href']
                date_str = time_tag.get('datetime')
                
                status_date = check_date_range(date_str)
                
                if status_date == 1:
                    continue
                elif status_date == 2:
                    print(f"    Ketemu berita lama ({date_str[:10]}). Misi Selesai.")
                    stop_signal = True
                    break
                
                if not is_relevant(title):
                    continue
                    
                res = save_to_db(title, link, date_str)
                if res == "SAVED":
                    print(f"    [{date_str[:10]}] {title[:50]}...")
                    total_saved += 1
            
            if stop_signal:
                break
            
            next_btn = soup.select_one('.block-more a')
            
            if next_btn and 'href' in next_btn.attrs:
                current_url = next_btn['href']
                page_num += 1
                time.sleep(1)
            else:
                print("    Tidak ada tombol 'Lihat Sebelumnya'. Halaman habis.")
                break
                
        except Exception as e:
            print(f" Error Network: {e}")
            break
    print("-" * 60)
    print(f" Selesai! Total berita Okt-Des 2025 tersimpan: {total_saved}")
if __name__ == "__main__":
    run_scraper()