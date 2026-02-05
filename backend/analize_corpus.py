
import os
from sqlalchemy import create_engine, text
from collections import Counter
import re
import json
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# ============================================================================
# BASIC STOPWORDS (Universal - bahasa Indonesia)
# ============================================================================
# Ini kata-kata yang PASTI stopword di bahasa manapun
UNIVERSAL_STOPWORDS = {
    # Kata hubung
    'dan', 'atau', 'tetapi', 'namun', 'sedangkan', 'kemudian', 'lalu', 'maka',
    'karena', 'sebab', 'jika', 'bila', 'kalau', 'apabila', 'agar', 'supaya',
    
    # Kata ganti
    'saya', 'aku', 'kamu', 'anda', 'ia', 'dia', 'mereka', 'kami', 'kita',
    'nya', 'mu', 'ku', 'beliau',
    
    # Kata keterangan
    'ini', 'itu', 'ini', 'disini', 'disana', 'disitu',
    'sangat', 'amat', 'terlalu', 'cukup', 'agak', 'lebih', 'kurang', 'paling',
    'sudah', 'belum', 'telah', 'akan', 'sedang', 'masih', 'pernah',
    'ada', 'tidak', 'bukan', 'tak', 'jangan',
    
    # Preposisi
    'di', 'ke', 'dari', 'pada', 'dalam', 'dengan', 'untuk', 'oleh', 'tentang',
    'terhadap', 'kepada', 'bagi', 'antara', 'atas', 'bawah', 'depan', 'belakang',
    
    # Kata bantu
    'yang', 'adalah', 'yaitu', 'yakni', 'ialah', 'merupakan', 'sebagai',
    'dapat', 'bisa', 'mampu', 'harus', 'wajib', 'perlu', 'mesti',
    'juga', 'pula', 'serta', 'bahkan', 'malah',
    
    # Kata tanya
    'apa', 'siapa', 'mana', 'kapan', 'dimana', 'kemana', 'mengapa', 'kenapa',
    'bagaimana', 'berapa',
    
    # Kata waktu umum
    'hari', 'kemarin', 'besok', 'nanti', 'sekarang', 'kini', 'dahulu',
    'tadi', 'lusa', 'dulu',
    
    # Angka
    'satu', 'dua', 'tiga', 'empat', 'lima', 'enam', 'tujuh', 'delapan',
    'sembilan', 'sepuluh', 'ratus', 'ribu', 'juta', 'miliar', 'triliun',
    'pertama', 'kedua', 'ketiga', 'keempat',
    
    # Kata umum tanpa makna
    'hal', 'cara', 'jenis', 'macam', 'bentuk', 'bagian', 'sisi', 'aspek',
}

# ============================================================================
# CORPUS ANALYSIS FUNCTIONS
# ============================================================================

def get_all_articles():
    """
    Ambil SEMUA artikel dari database yang punya konten
    """
    with engine.connect() as conn:
        query = text("""
            SELECT id, title, content, sentiment_label
            FROM articles 
            WHERE content IS NOT NULL AND content != ''
            ORDER BY created_at DESC
        """)
        result = conn.execute(query)
        return result.fetchall()


def clean_text_basic(text):
    """
    Cleaning dasar - tanpa stopword filtering
    """
    if not text:
        return []
    
    text = text.lower()
    
    text = re.sub(r'http\S+|www\S+', '', text)
    
    text = re.sub(r'\S+@\S+', '', text)
    
    text = re.sub(r'\b\d+\b', '', text)
    
    text = re.sub(r'[^a-z\s]', ' ', text)
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    words = text.split()
    
    words = [w for w in words if len(w) >= 3]
    
    return words


def extract_ngrams_basic(words, n=2):
    """
    Extract n-grams tanpa filtering
    """
    ngrams = []
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        ngrams.append(ngram)
    return ngrams


def analyze_corpus():
    """
    MAIN ANALYSIS FUNCTION
    Analyze seluruh corpus dan identifikasi stopwords candidates
    """
    print("\n" + "="*80)
    print("CORPUS ANALYZER - Generating Data-Driven Stopwords")
    print("="*80)
    
    print("\n[1/6] Fetching articles from database...")
    articles = get_all_articles()
    total_articles = len(articles)
    
    if total_articles == 0:
        print("❌ No articles found in database!")
        return None
    
    print(f"✅ Found {total_articles} articles")
    
    print("\n[2/6] Extracting words and n-grams...")
    
    all_unigrams = []
    all_bigrams = []
    all_trigrams = []
    
    doc_word_sets = []
    
    for i, article in enumerate(articles, 1):
        if i % 100 == 0:
            print(f"   Processing: {i}/{total_articles} articles...")
        
        full_text = f"{article.title} {article.content}"
        
        words = clean_text_basic(full_text)
        
        all_unigrams.extend(words)
        
        bigrams = extract_ngrams_basic(words, 2)
        all_bigrams.extend(bigrams)
        
        trigrams = extract_ngrams_basic(words, 3)
        all_trigrams.extend(trigrams)
        
        doc_word_sets.append(set(words))
    
    print(f"✅ Extracted {len(all_unigrams):,} unigrams")
    print(f"✅ Extracted {len(all_bigrams):,} bigrams")
    print(f"✅ Extracted {len(all_trigrams):,} trigrams")
    
    print("\n[3/6] Calculating word frequencies...")
    
    unigram_freq = Counter(all_unigrams)
    bigram_freq = Counter(all_bigrams)
    trigram_freq = Counter(all_trigrams)
    
    print(f"✅ Unique unigrams: {len(unigram_freq):,}")
    print(f"✅ Unique bigrams: {len(bigram_freq):,}")
    print(f"✅ Unique trigrams: {len(trigram_freq):,}")
    
    print("\n[4/6] Calculating document frequencies...")
")
    
    doc_freq = {}
    unique_words = set(all_unigrams)
    
    for word in unique_words:
        doc_freq[word] = sum(1 for doc_set in doc_word_sets if word in doc_set)
    
    print("\n[5/6] Identifying stopwords candidates...")
    
    stopwords_candidates = set(UNIVERSAL_STOPWORDS)
    
    threshold_too_common = total_articles * 0.70
    too_common_words = {
        word for word, df in doc_freq.items() 
        if df > threshold_too_common and word not in UNIVERSAL_STOPWORDS
    }
    
    print(f"   📊 Words appearing in >70% articles: {len(too_common_words)}")
    
    total_words = len(all_unigrams)
    high_freq_threshold = total_words * 0.001  # 0.1% dari total kata
    
    very_frequent_words = {
        word for word, freq in unigram_freq.items()
        if freq > high_freq_threshold and word not in UNIVERSAL_STOPWORDS
    }
    
    print(f"   📊 Very high frequency words: {len(very_frequent_words)}")
    
    news_structure_words = set()
    news_patterns = [
        'berita', 'artikel', 'foto', 'video', 'gambar', 'sumber', 'reporter',
        'wartawan', 'redaksi', 'editor', 'koresponden', 'kontributor',
        'baca', 'selengkapnya', 'klik', 'lihat', 'simak', 'menyimak',
        'dokumentasi', 'ilustrasi', 'caption', 'kutipan', 'dikutip',
        'wib', 'wit', 'wita', 'tanggal', 'jam', 'pukul',
    ]
    
    for word in unigram_freq.keys():
        for pattern in news_patterns:
            if pattern in word or word in pattern:
                news_structure_words.add(word)
    
    print(f"   📊 News structure words: {len(news_structure_words)}")
    
    generic_location_words = set()
    generic_patterns = [
        'aceh', 'banda', 'provinsi', 'kabupaten', 'kota', 'daerah',
        'pemerintah', 'pemprov', 'pemkab', 'pemkot',
        'dinas', 'badan', 'kantor', 'lembaga', 'instansi',
        'utara', 'selatan', 'barat', 'timur', 'tengah', 'pusat',
    ]
    
    for word in unigram_freq.keys():
        for pattern in generic_patterns:
            if word == pattern or (len(word) <= 6 and pattern in word):
                generic_location_words.add(word)
    
    print(f"   📊 Generic location/institution words: {len(generic_location_words)}")
    
    stopwords_candidates.update(too_common_words)
    stopwords_candidates.update(very_frequent_words)
    stopwords_candidates.update(news_structure_words)
    stopwords_candidates.update(generic_location_words)
    
    print(f"\n✅ Total stopwords candidates: {len(stopwords_candidates)}")
    
    print("\n[6/6] Generating reports and important keywords...")
    
    important_keywords = []
    
    for word, freq in unigram_freq.most_common(200):
        if word not in stopwords_candidates and len(word) > 3:
            important_keywords.append({
                'word': word,
                'frequency': freq,
                'doc_frequency': doc_freq[word],
                'percentage': round((doc_freq[word] / total_articles) * 100, 1)
            })
    
    important_keywords = important_keywords[:100]
    
    print(f"✅ Identified {len(important_keywords)} important keywords")
    
    results = {
        'corpus_stats': {
            'total_articles': total_articles,
            'total_words': total_words,
            'unique_unigrams': len(unigram_freq),
            'unique_bigrams': len(bigram_freq),
            'unique_trigrams': len(trigram_freq),
        },
        'stopwords': sorted(list(stopwords_candidates)),
        'important_keywords': important_keywords,
        'top_bigrams': [
            {'text': bg, 'frequency': freq}
            for bg, freq in bigram_freq.most_common(50)
            if not any(stop in bg for stop in stopwords_candidates)
        ],
        'top_trigrams': [
            {'text': tg, 'frequency': freq}
            for tg, freq in trigram_freq.most_common(30)
            if not any(stop in tg for stop in stopwords_candidates)
        ],
    }
    
    return results


def save_analysis_results(results):
    """
    Save hasil analysis ke file JSON
    """
    if not results:
        print("❌ No results to save!")
        return
    
    stopwords_file = "stopwords_aceh.json"
    with open(stopwords_file, 'w', encoding='utf-8') as f:
        json.dump({
            'stopwords': results['stopwords'],
            'generated_at': __import__('datetime').datetime.now().isoformat(),
            'corpus_stats': results['corpus_stats']
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Stopwords saved to: {stopwords_file}")
    
    report_file = "corpus_analysis_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Full report saved to: {report_file}")
    
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"\n📊 Corpus Statistics:")
    print(f"   - Total Articles: {results['corpus_stats']['total_articles']:,}")
    print(f"   - Total Words: {results['corpus_stats']['total_words']:,}")
    print(f"   - Unique Words: {results['corpus_stats']['unique_unigrams']:,}")
    
    print(f"\n🚫 Stopwords Generated: {len(results['stopwords'])} words")
    print(f"   Preview (first 30):")
    for i, word in enumerate(results['stopwords'][:30], 1):
        print(f"   {word}", end='  ')
        if i % 6 == 0:
            print()
    
    print(f"\n\n✨ Important Keywords (Top 20):")
    print(f"   {'Keyword':<20} {'Frequency':>10} {'In % Articles':>15}")
    print(f"   {'-'*20} {'-'*10} {'-'*15}")
    for item in results['important_keywords'][:20]:
        print(f"   {item['word']:<20} {item['frequency']:>10,} {item['percentage']:>14.1f}%")
    
    print(f"\n🔗 Top Bigrams (meaningful phrases):")
    for i, item in enumerate(results['top_bigrams'][:15], 1):
        print(f"   {i:2d}. {item['text']:<35} ({item['frequency']:>4,}x)")
    
    print(f"\n🔗 Top Trigrams (3-word phrases):")
    for i, item in enumerate(results['top_trigrams'][:10], 1):
        print(f"   {i:2d}. {item['text']:<40} ({item['frequency']:>4,}x)")
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the generated stopwords in: stopwords_aceh.json")
    print("2. Check the important keywords - are they relevant?")
    print("3. Use stopwords_aceh.json in wordcloud_generator_v2.py")
    print("="*80 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    try:
        results = analyze_corpus()
        
        if results:
            save_analysis_results(results)
        else:
            print("\n❌ Analysis failed - no results generated")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()