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

def get_unscraped_hra():
    """Ambil berita HRA yang isinya masih kosong"""
    with engine.connect() as conn:
        # Filter khusus source 'harianrakyataceh.com'
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

        # 1. Cari Wadah Utama (Class: the-content)
        container = soup.select_one('.the-content')
        
        if not container:
            return "[GAGAL] Class '.the-content' tidak ditemukan."

        # 2. BERSIH-BERSIH (Hapus elemen sampah)
        # Hapus Iklan (class funds)
        for ad in container.select('.funds'):
            ad.decompose()
            
        # Hapus Berita Terkait (class related-box)
        for related in container.select('.related-box'):
            related.decompose()

        # Hapus Info Editor (class meta-info)
        for meta in container.select('.meta-info'):
            meta.decompose()

        # Hapus Script & Style
        for script in container(["script", "style", "iframe"]):
            script.decompose()

        # 3. Ambil Teks dari Paragraf Tersisa
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
            print("✅ Semua berita Harian Rakyat Aceh sudah discrape isinya.")
            break

        print(f"🔄 Memproses {len(tasks)} antrian HRA...")
        
        for row in tasks:
            a_id, url, title = row
            print(f"   - Menyedot: {title[:30]}...")
            
            content = scrape_hra_body(url)
            
            if "GAGAL" not in content and "ERROR" not in content:
                update_content(a_id, content)
                print("     ✅ OK")
            else:
                print(f"     ❌ {content}")
                # Tandai error di DB supaya tidak diloop terus (opsional, saat ini biarkan NULL)

            time.sleep(random.uniform(1, 3)) # Sopan santun

if __name__ == "__main__":
    run()