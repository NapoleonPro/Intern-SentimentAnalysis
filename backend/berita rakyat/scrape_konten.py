import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
import time
import random

# --- KONFIGURASI DATABASE ---
DB_USER = 'postgres'
DB_PASS = 'admin' 
DB_NAME = 'db_pkp_aceh'
DB_HOST = 'localhost'
DB_PORT = '5432'

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# --- KAMUS SELECTOR (Agar bisa baca berbagai web) ---
# Script akan mencoba satu per satu sampai ketemu isinya
CONTENT_SELECTORS = [
    # 1. Selector Khusus NOA.co.id
    {'id': 'single-article-text'}, 
    
    # 2. Selector Khusus BeritaRakyatAceh (WordPress Standard)
    {'class_': 'entry-content'},
    
    # 3. Selector Cadangan Umum (Jaga-jaga)
    {'class_': 'post-content'},
    {'class_': 'article-content'},
    {'class_': 'detail-text'},
    {'tag': 'article'} # Terakhir, ambil seluruh tag article kalau kepepet
]

def get_unscraped_articles():
    """Ambil daftar berita yang kontennya masih kosong (NULL)"""
    with engine.connect() as conn:
        # Ambil max 10 biar tidak terlalu berat sekali jalan
        query = text("SELECT id, url, title FROM articles WHERE content IS NULL ORDER BY created_at DESC LIMIT 10")
        return conn.execute(query).fetchall()

def update_content(article_id, content_text):
    """Simpan teks berita ke database"""
    with engine.connect() as conn:
        query = text("UPDATE articles SET content = :c WHERE id = :id")
        conn.execute(query, {"c": content_text, "id": article_id})
        conn.commit()

def fetch_body(url):
    """Fungsi download isi berita dengan selector pintar"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Hapus elemen sampah (iklan, script, style) sebelum mengambil teks
        for script in soup(["script", "style", "iframe", "noscript"]):
            script.decompose()

        # LOOPING MENCARI SELECTOR YANG COCOK
        found_text = ""
        
        for selector in CONTENT_SELECTORS:
            element = None
            
            # Cek jenis selector (ID atau Class atau Tag)
            if 'id' in selector:
                element = soup.find(id=selector['id'])
            elif 'class_' in selector:
                element = soup.find(class_=selector['class_'])
            elif 'tag' in selector:
                element = soup.find(selector['tag'])
            
            # Jika ketemu, ambil teksnya dan berhenti mencari
            if element:
                # Ambil semua paragraf <p> biar rapi
                paragraphs = element.find_all('p')
                if paragraphs:
                    found_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
                else:
                    # Kalau tidak ada <p>, ambil teks mentah
                    found_text = element.get_text(strip=True)
                
                # Jika teksnya terlalu pendek (misal cuma "Share this"), anggap gagal dan cari lagi
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
        print("✅ Semua berita sudah discrape. Tidak ada antrian.")
        return

    print(f"Memulai Content Scraping Universal. Ada {len(tasks)} artikel antri.")
    print("-" * 60)

    for i, row in enumerate(tasks):
        a_id, url, title = row
        print(f"[{i+1}/{len(tasks)}] Menyedot: {title[:40]}...")
        
        content = fetch_body(url)
        
        # Simpan ke DB
        if content and "[ERROR]" not in content and "[GAGAL]" not in content:
            update_content(a_id, content)
            print("   ✅ Berhasil disimpan.")
        else:
            print(f"   ❌ Gagal: {content[:50]}...")
            # Opsional: Tandai error di DB biar tidak diulang terus, tapi skip dulu

        # Jeda biar server orang tidak marah (sopan santun bot)
        time.sleep(random.uniform(1, 3))

    print("-" * 60)
    print("Selesai.")

if __name__ == "__main__":
    scrape_body()