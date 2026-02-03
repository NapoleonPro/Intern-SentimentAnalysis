import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from datetime import datetime
import time
import random
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

# Target: Pencarian "Pemerintah Aceh"
BASE_URL = "https://kabaracehonline.com"
SEARCH_QUERY = "pemerintah+aceh"
CUTOFF_DAYS = 90 # 3 Bulan terakhir

# Kamus Bulan Indo
ID_MONTHS = {
    'januari': '01', 'februari': '02', 'maret': '03', 'april': '04',
    'mei': '05', 'juni': '06', 'juli': '07', 'agustus': '08',
    'september': '09', 'oktober': '10', 'november': '11', 'desember': '12'
}

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def parse_indonesian_date(date_str):
    """
    Format: "28 November 2025" -> "2025-11-28"
    """
    if not date_str: return None
    try:
        clean_str = date_str.lower().strip()
        # Hapus spasi ganda/karakter aneh
        clean_str = re.sub(r'\s+', ' ', clean_str)
        
        parts = clean_str.split()
        if len(parts) < 3: return None
        
        day = parts[0].zfill(2)
        month_name = parts[1]
        year = parts[2]
        
        month_num = ID_MONTHS.get(month_name)
        if not month_num: return None
        
        return datetime.fromisoformat(f"{year}-{month_num}-{day}")
    except:
        return None

def check_date(date_obj):
    if not date_obj: return 2
    now = datetime.now()
    delta = now - date_obj
    if delta.days <= CUTOFF_DAYS:
        return 0 # OK
    else:
        return 1 # Tua

def save_to_db(title, url, date_obj):
    try:
        with engine.connect() as conn:
            check = conn.execute(text("SELECT id FROM articles WHERE url = :u"), {"u": url}).fetchone()
            if check: return "DUPLICATE"

            query = text("""
                INSERT INTO articles (title, url, published_date, source, created_at)
                VALUES (:t, :u, :d, 'kabaracehonline.com', NOW())
            """)
            conn.execute(query, {"t": title, "u": url, "d": date_obj})
            conn.commit()
            return "SAVED"
    except Exception as e:
        print(f"   [Error DB] {e}")
        return "ERROR"

def run_scraper():
    page = 1
    total_saved = 0
    keep_going = True
    
    print(f"🚀 Memulai Scrape Kabar Aceh Online: {BASE_URL}")
    print("-" * 60)

    while keep_going:
        # Pola Pagination: /page/2/?s=...
        if page == 1:
            url = f"{BASE_URL}/?s={SEARCH_QUERY}"
        else:
            url = f"{BASE_URL}/page/{page}/?s={SEARCH_QUERY}"
            
        print(f"\n📄 Membuka Halaman {page}...")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}
            resp = requests.get(url, headers=headers, timeout=20) # Timeout agak lamaan dikit
            
            if resp.status_code == 404:
                print("   ⚠️ Halaman Habis (404).")
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Selector Artikel (Elementor Post)
            articles = soup.select('article.elementor-post')
            
            if not articles:
                print("   ⚠️ Tidak ada artikel di halaman ini.")
                break
            
            old_articles_on_page = 0
            
            for item in articles:
                # 1. Judul & Link
                title_tag = item.select_one('h3.elementor-post__title a')
                if not title_tag: continue
                
                title = title_tag.get_text(strip=True)
                link = title_tag['href']
                
                # 2. Tanggal
                date_tag = item.select_one('.elementor-post-date')
                raw_date = date_tag.get_text(strip=True) if date_tag else ""
                
                date_obj = parse_indonesian_date(raw_date)
                
                # Cek Umur
                date_status = check_date(date_obj)
                
                if date_status == 1: # Tua
                    old_articles_on_page += 1
                    continue
                elif date_status == 2: # Error tanggal
                    continue
                
                # Filter Judul (Opsional, biar makin akurat)
                if not any(x in title.lower() for x in ['pemerintah', 'pemprov', 'gubernur', 'wagub', 'sekda', 'aceh']):
                    continue

                # Simpan
                status = save_to_db(title, link, date_obj)
                if status == "SAVED":
                    print(f"   ✅ [{raw_date}] {title[:40]}...")
                    total_saved += 1
                elif status == "DUPLICATE":
                    # print(f"   zzz Duplikat: {title[:20]}...")
                    pass
            
            # Stop jika semua tua
            if old_articles_on_page == len(articles):
                print(f"   🛑 Semua berita di halaman {page} sudah usang. Stop.")
                keep_going = False
                break
            
            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"❌ Error: {e}")
            break

    print("-" * 60)
    print(f"🏁 Selesai. Total tersimpan: {total_saved}")

if __name__ == "__main__":
    run_scraper()