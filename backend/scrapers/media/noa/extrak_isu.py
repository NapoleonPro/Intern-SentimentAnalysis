from sqlalchemy import create_engine, text
from collections import Counter
import re
DB_USER = 'postgres'
DB_PASS = 'admin'
DB_NAME = 'db_pkp_aceh'
STOPWORDS = {
    'dan', 'yang', 'di', 'ke', 'dari', 'ini', 'itu', 'untuk', 'pada', 'adalah',
    'sebagai', 'dengan', 'dalam', 'juga', 'akan', 'sudah', 'saya', 'kami', 'kita',
    'mereka', 'dia', 'ia', 'bisa', 'ada', 'tidak', 'saat', 'oleh', 'telah',
    'bahwa', 'secara', 'karena', 'agar', 'banyak', 'sangat', 'lebih', 'atau',
    'pemerintah', 'aceh', 'tersebut', 'menjadi', 'dapat', 'kata', 'kepada',
    'hari', 'tahun', 'wib', 'lalu', 'masyarakat', 'provinsi', 'kabupaten',
    'ketua', 'kepala', 'dinas', 'banda', 'besar', 'barat', 'utara', 'timur'
}
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}')
def clean_text(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text).lower()
    words = text.split()
    return [w for w in words if w not in STOPWORDS and len(w) > 3]
def get_negative_news():
    with engine.connect() as conn:
        query = text("SELECT title, content FROM articles WHERE sentiment_label = 'Negatif'")
        return conn.execute(query).fetchall()
def generate_warning():
    print("GENERATING EARLY WARNING REPORT...")
    print("=" * 50)
    
    neg_articles = get_negative_news()
    
    if not neg_articles:
        print("Aman terkendali. Tidak ada isu negatif ditemukan.")
        return
    all_words = []
    
    print(f"DITEMUKAN {len(neg_articles)} ISU POTENSIAL:\n")
    
    for i, row in enumerate(neg_articles):
        judul = row[0]
        isi = row[1]
        
        words = clean_text(f"{judul} {isi}")
        all_words.extend(words)
        
        print(f"{i+1}. {judul}")
        print(f"Cuplikan: {isi[:150]}...")
        print("-" * 30)
    word_counts = Counter(all_words)
    top_keywords = word_counts.most_common(10)
    
    print("\nKATA KUNCI DOMINAN (ISU UTAMA):")
    for word, count in top_keywords:
        print(f"{word}: muncul {count} kali")
    print("=" * 50)
    
    if top_keywords:
        top_topic = top_keywords[0][0].upper()
        print(f"Suggestion: Isu utama tampaknya terkait '{top_topic}'")
if __name__ == "__main__":
    generate_warning()