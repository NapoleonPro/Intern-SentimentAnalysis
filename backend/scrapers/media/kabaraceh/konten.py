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

def get_unscraped_ka():
    with engine.connect() as conn:
        query = text("""
            SELECT id, url, title 
            FROM articles 
            WHERE source = 'kabaracehonline.com' 
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
    # Header lebih lengkap biar tidak ditolak server
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'en-US,en;q=0.9,id;q=0.8'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # --- STRATEGI JALA IKAN (Multi-Selector) ---
        # Kita coba satu-satu dari yang paling spesifik
        possible_selectors = [
            '.entry-content-single',          # Khas tema Kentooz/BloggingPro
            '.entry-content',                 # Standar WordPress
            '.elementor-widget-theme-post-content', # Jika full Elementor
            'article',                        # Fallback kasar
            '#content'                        # Fallback terakhir
        ]

        container = None
        used_selector = ""

        for selector in possible_selectors:
            container = soup.select_one(selector)
            if container:
                used_selector = selector
                # Cek apakah container ini punya cukup teks (minimal 100 karakter)
                if len(container.get_text(strip=True)) > 100:
                    break
        
        if not container:
            return "[GAGAL] Semua selector tidak mempan."

        # --- BERSIH-BERSIH ---
        # Hapus elemen pengganggu di dalam berita
        hapus_list = [
            'script', 'style', 'iframe', 
            '.sharedaddy',          # Tombol share
            '.related-posts',       # Berita terkait
            '.jp-relatedposts',     # Jetpack related
            '.adsbygoogle',         # Iklan
            '.gmr-banner',          # Banner iklan tema
            '.wp-caption',          # Caption gambar (opsional, kadang teksnya duplikat)
            '.meta-info'            # Info editor/penulis di bawah
        ]
        
        for css_class in hapus_list:
            for tag in container.select(css_class):
                tag.decompose()

        paragraphs = container.find_all(['p', 'div']) # Kadang teks ada di div di Elementor
        
        cleaned_text = []
        for p in paragraphs:
            txt = p.get_text(strip=True)
            # Filter paragraf sampah pendek yang lolos
            if len(txt) > 20 and "Baca Juga" not in txt: 
                cleaned_text.append(txt)
        
        text_content = "\n\n".join(cleaned_text)
        
        if not text_content: return "[GAGAL] Teks kosong setelah pembersihan."
        
        return text_content

    except Exception as e:
        return f"[ERROR] {e}"

def run():
    tasks = get_unscraped_ka()
    print(f"🚀 Memproses {len(tasks)} antrian Kabar Aceh Online...")
    
    for i, row in enumerate(tasks):
        print(f"[{i+1}/{len(tasks)}] {row.title[:40]}...")
        content = fetch_body(row.url)
        
        if "GAGAL" not in content and "ERROR" not in content:
            update_content(row.id, content)
            print("   ✅ OK")
        else:
            print(f"   ❌ {content}")
        
        # Jeda random agak lama biar gak diputus koneksi lagi
        time.sleep(random.uniform(2, 4))

if __name__ == "__main__":
    run()