import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
import time
import os
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
MEDIA_NAME = 'NOA'
BASE_URL = "https://www.noa.co.id/?s=pemerintah+aceh"
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}')
def get_media_id():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM media_sources WHERE name = :name"), {"name": MEDIA_NAME})
        row = result.fetchone()
        if row: return row[0]
        else:
            print(f"Media '{MEDIA_NAME}' tidak ditemukan! Cek tabel media_sources.")
            exit()
def parse_date(date_str):
    bulan_indo = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'Mei': '05', 'Jun': '06',
        'Jul': '07', 'Ags': '08', 'Sep': '09', 'Okt': '10', 'Nov': '11', 'Des': '12'
    }
    try:
        parts = date_str.split(',')[-1].split('-')[0].strip().split()
        day = parts[0].zfill(2)
        month_str = parts[1]
        month = bulan_indo.get(month_str, '00')
        year = parts[2]
        return f"{year}-{month}-{day}", year, month
    except:
        return None, None, None
def scrape_links():
    media_id = get_media_id()
    current_url = BASE_URL
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    print(f"Memulai scraping (Filter: Okt-Des 2025)...")
    stop_scraping = False
    pages_processed = 0
    while current_url and not stop_scraping:
        print(f"Halaman {pages_processed + 1}: {current_url}")
        try:
            response = requests.get(current_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('div', class_='search-list')
            
            if not articles:
                print("Tidak ada artikel.")
                break
            count_saved = 0
            for item in articles:
                try:
                    text_div = item.find('div', class_='search-text')
                    title = text_div.find('a').find('h2').get_text(strip=True)
                    url = text_div.find('a')['href']
                    
                    date_tag = text_div.find('p', class_='search-tanggal').find('span')
                    date_raw = date_tag.get_text(strip=True)
                    
                    clean_date, year, month = parse_date(date_raw)
                    
                    if not clean_date: continue
                    if year == '2025':
                        if month in ['10', '11', '12']:
                            with engine.connect() as conn:
                                cek = conn.execute(text("SELECT id FROM articles WHERE url = :url"), {"url": url}).fetchone()
                                if not cek:
                                    query = text("INSERT INTO articles (media_id, title, url, published_date, created_at) VALUES (:mid, :title, :url, :date, NOW())")
                                    conn.execute(query, {"mid": media_id, "title": title, "url": url, "date": clean_date})
                                    conn.commit()
                                    count_saved += 1
                                    print(f"[Tersimpan] {clean_date} | {title[:30]}...")
                                else:
                                    print(f"[Skip-Ada] {clean_date} | {title[:30]}...")
                        else:
                            if int(month) < 10:
                                print(f"Ketemu berita lama ({clean_date}). Stop scraping.")
                                stop_scraping = True
                                break
                    elif int(year) < 2025:
                        print(f"Ketemu tahun lama ({year}). Stop scraping.")
                        stop_scraping = True
                        break
                except Exception as e:
                    continue
            next_div = soup.find('div', class_='next')
            if next_div and next_div.find('a') and not stop_scraping:
                current_url = next_div.find('a')['href']
                pages_processed += 1
                time.sleep(1)
            else:
                current_url = None
        except Exception as e:
            print(f"Error: {e}")
            break
    print("Selesai scraping.")
if __name__ == "__main__":
    scrape_links()