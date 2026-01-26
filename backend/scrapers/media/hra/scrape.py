import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from datetime import datetime
import time
import random

# --- KONFIGURASI DATABASE ---
DB_USER = 'postgres'
DB_PASS = 'admin' 
DB_NAME = 'db_pkp_aceh'
DB_HOST = 'localhost'
DB_PORT = '5432'

# Target: Pencarian "Pemerintah Aceh"
BASE_URL = "https://harianrakyataceh.com/search/?q=pemerintah+aceh"

# KEYWORD FILTER (Opsional, biar makin relevan)
MUST_HAVE_KEYWORDS = ["pemerintah", "pemprov", "gubernur", "wagub", "sekda", "aceh"]

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def is_relevant(title):
    title_lower = title.lower()
    for kw in MUST_HAVE_KEYWORDS:
        if kw in title_lower:
            return True
    return False

def check_date_range(date_str):
    """
    Return Code:
    0 = Target (Okt - Des 2025) -> SIMPAN
    1 = Terlalu Baru (Jan 2026 ke atas) -> SKIP
    2 = Terlalu Lama (Sep 2025 ke bawah) -> STOP
    """
    if not date_str: return 1 # Asumsikan baru kalau gak ada tanggal
    
    try:
        # Format HTML: 2026-01-25T17:20:27+07:00
        dt = datetime.fromisoformat(date_str)
        
        # Batas Waktu
        start_date = datetime(2025, 10, 1, tzinfo=dt.tzinfo) # 1 Okt 2025
        end_date = datetime(2025, 12, 31, 23, 59, 59, tzinfo=dt.tzinfo) # 31 Des 2025
        
        if dt > end_date:
            return 1 # Terlalu Baru (Jan 2026)
        elif start_date <= dt <= end_date:
            return 0 # Masuk Target!
        else:
            return 2 # Terlalu Lama (STOP)
            
    except Exception as e:
        print(f"   [Warn] Gagal parse tanggal: {e}")
        return 1

def save_to_db(title, url, date_str):
    try:
        with engine.connect() as conn:
            # Cek duplikat
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
    # URL Awal
    current_url = BASE_URL
    total_saved = 0
    page_num = 1
    
    print(f"🚀 Memulai Scrape Harian Rakyat Aceh")
    print(f"   Target: 1 Oktober 2025 - 31 Desember 2025")
    print("-" * 60)

    while current_url:
        print(f"\n📄 Memproses Halaman {page_num}...")
        # print(f"   URL: {current_url}")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}
            resp = requests.get(current_url, headers=headers, timeout=15)
            
            if resp.status_code != 200:
                print("   ⚠️ Halaman tidak bisa dibuka. Berhenti.")
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 1. Ambil List Artikel
            articles = soup.select('article')
            
            if not articles:
                print("   ⚠️ Tidak ada artikel ditemukan. Selesai.")
                break
                
            stop_signal = False
            
            for item in articles:
                # Ambil Elemen
                title_tag = item.select_one('a.title')
                time_tag = item.select_one('time')
                
                if not title_tag or not time_tag:
                    continue
                    
                title = title_tag.get_text(strip=True)
                link = title_tag['href']
                date_str = time_tag.get('datetime')
                
                # Cek Tanggal
                status_date = check_date_range(date_str)
                
                if status_date == 1:
                    # Terlalu Baru (Jan 2026), skip aja
                    # print(f"   [Skip - 2026] {title[:30]}...")
                    continue
                elif status_date == 2:
                    # Terlalu Lama (Sept 2025), STOP TOTAL
                    print(f"   🛑 Ketemu berita lama ({date_str[:10]}). Misi Selesai.")
                    stop_signal = True
                    break
                
                # Cek Keyword (Biar gak sampah masuk)
                if not is_relevant(title):
                    continue
                    
                # Simpan ke DB
                res = save_to_db(title, link, date_str)
                if res == "SAVED":
                    print(f"   ✅ [{date_str[:10]}] {title[:50]}...")
                    total_saved += 1
            
            if stop_signal:
                break
            
            # 2. Cari Halaman Berikutnya (Pagination)
            # Selector dari HTML kamu: <div class="block-more"> <a href="...">
            next_btn = soup.select_one('.block-more a')
            
            if next_btn and 'href' in next_btn.attrs:
                current_url = next_btn['href']
                page_num += 1
                time.sleep(1) # Istirahat bentar
            else:
                print("   ⚠️ Tidak ada tombol 'Lihat Sebelumnya'. Halaman habis.")
                break
                
        except Exception as e:
            print(f"❌ Error Network: {e}")
            break

    print("-" * 60)
    print(f"🏁 Selesai! Total berita Okt-Des 2025 tersimpan: {total_saved}")

if __name__ == "__main__":
    run_scraper()