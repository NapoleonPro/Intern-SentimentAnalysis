"""
WORD CLOUD GENERATOR V2 - Data-Driven Edition
Menggunakan stopwords yang di-generate dari analyze_corpus.py
"""

import os
from sqlalchemy import create_engine, text
from collections import Counter
import re
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# ============================================================================
# LOAD STOPWORDS FROM ANALYSIS
# ============================================================================

def load_stopwords(filepath="stopwords_aceh.json"):
    """
    Load stopwords yang sudah di-generate dari analyze_corpus.py
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stopwords = set(data['stopwords'])
        
        print(f"✅ Loaded {len(stopwords)} stopwords from: {filepath}")
        print(f"   Generated at: {data.get('generated_at', 'unknown')}")
        print(f"   Based on {data['corpus_stats']['total_articles']} articles")
        
        return stopwords
    
    except FileNotFoundError:
        print(f"❌ Stopwords file not found: {filepath}")
        print(f"   Please run 'analyze_corpus.py' first to generate stopwords!")
        return set()
    except Exception as e:
        print(f"❌ Error loading stopwords: {e}")
        return set()


# Global stopwords (akan di-load saat runtime)
STOPWORDS = set()


# ============================================================================
# TEXT PROCESSING FUNCTIONS
# ============================================================================

def clean_text(text):
    """
    Membersihkan teks dari karakter khusus dan noise
    """
    if not text:
        return []
    
    # Lowercase
    text = text.lower()
    
    # Hapus URL
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Hapus email
    text = re.sub(r'\S+@\S+', '', text)
    
    # Hapus angka standalone (tapi tetap pertahankan dalam kata)
    text = re.sub(r'\b\d+\b', '', text)
    
    # Hapus karakter khusus, pertahankan huruf dan spasi
    text = re.sub(r'[^a-z\s]', ' ', text)
    
    # Hapus spasi berlebih
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Tokenize
    words = text.split()
    
    # Filter: minimal 3 karakter, bukan stopword
    words = [w for w in words if len(w) >= 3 and w not in STOPWORDS]
    
    return words


def extract_ngrams(words, n=2):
    """
    Ekstrak n-gram dari list kata
    n=2 untuk bigram, n=3 untuk trigram
    """
    ngrams = []
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        # Pastikan tidak ada stopword dalam n-gram
        ngram_words = words[i:i+n]
        if not any(w in STOPWORDS for w in ngram_words):
            ngrams.append(ngram)
    return ngrams


def calculate_term_frequencies(documents, include_unigrams=True, include_bigrams=True, include_trigrams=True):
    """
    Hitung frekuensi term dari semua dokumen
    
    Parameters:
    - documents: list of text content
    - include_unigrams: apakah include kata tunggal
    - include_bigrams: apakah include 2-word phrases
    - include_trigrams: apakah include 3-word phrases
    
    Returns:
    - Counter object dengan term frequencies
    """
    all_terms = []
    
    for doc in documents:
        words = clean_text(doc)
        
        # Unigrams (kata tunggal)
        if include_unigrams:
            # Filter kata tunggal yang terlalu pendek
            unigrams = [w for w in words if len(w) >= 4]
            all_terms.extend(unigrams)
        
        # Bigrams (2 kata)
        if include_bigrams:
            bigrams = extract_ngrams(words, 2)
            all_terms.extend(bigrams)
        
        # Trigrams (3 kata)
        if include_trigrams:
            trigrams = extract_ngrams(words, 3)
            all_terms.extend(trigrams)
    
    return Counter(all_terms)


def filter_by_frequency(term_counter, min_freq=3, max_freq_percentile=95):
    """
    Filter term berdasarkan frekuensi:
    - Buang yang terlalu jarang (< min_freq)
    - Buang yang terlalu sering (> percentile tertentu, mungkin noise)
    
    Parameters:
    - term_counter: Counter object
    - min_freq: frekuensi minimum
    - max_freq_percentile: percentile untuk upper bound (0-100)
    
    Returns:
    - Filtered Counter object
    """
    if not term_counter:
        return Counter()
    
    # Calculate max frequency threshold
    all_freqs = sorted(term_counter.values(), reverse=True)
    if len(all_freqs) > 0:
        percentile_index = int(len(all_freqs) * (max_freq_percentile / 100))
        max_freq = all_freqs[min(percentile_index, len(all_freqs) - 1)]
    else:
        max_freq = float('inf')
    
    # Filter
    filtered = Counter({
        term: freq for term, freq in term_counter.items()
        if min_freq <= freq <= max_freq
    })
    
    return filtered


# ============================================================================
# DATABASE QUERIES
# ============================================================================

def get_articles_by_date(start_date=None, end_date=None, sentiment=None):
    """
    Ambil artikel dari database berdasarkan filter
    """
    with engine.connect() as conn:
        # Build query dinamis
        conditions = ["content IS NOT NULL", "content != ''"]
        params = {}
        
        if start_date:
            conditions.append("published_date >= :start_date")
            params['start_date'] = start_date
        
        if end_date:
            conditions.append("published_date <= :end_date")
            params['end_date'] = end_date
        
        if sentiment:
            conditions.append("sentiment_label = :sentiment")
            params['sentiment'] = sentiment
        
        where_clause = " AND ".join(conditions)
        
        query_str = f"""
            SELECT id, title, content, published_date, sentiment_label
            FROM articles 
            WHERE {where_clause}
            ORDER BY published_date DESC
        """
        
        result = conn.execute(text(query_str), params)
        return result.fetchall()


def get_articles_by_month(year, month, sentiment=None):
    """
    Ambil artikel berdasarkan bulan tertentu
    """
    with engine.connect() as conn:
        conditions = [
            "content IS NOT NULL",
            "content != ''",
            "EXTRACT(YEAR FROM published_date) = :year",
            "EXTRACT(MONTH FROM published_date) = :month"
        ]
        params = {'year': year, 'month': month}
        
        if sentiment:
            conditions.append("sentiment_label = :sentiment")
            params['sentiment'] = sentiment
        
        where_clause = " AND ".join(conditions)
        
        query_str = f"""
            SELECT id, title, content, published_date, sentiment_label
            FROM articles 
            WHERE {where_clause}
            ORDER BY published_date DESC
        """
        
        result = conn.execute(text(query_str), params)
        return result.fetchall()


# ============================================================================
# WORD CLOUD GENERATION
# ============================================================================

def generate_wordcloud_data(
    start_date=None, 
    end_date=None, 
    year=None, 
    month=None, 
    sentiment=None,
    top_n=50,
    include_unigrams=True,
    include_bigrams=True,
    include_trigrams=True,
    min_frequency=3
):
    """
    Generate word cloud data dengan data-driven stopwords
    
    Parameters:
    - start_date, end_date: untuk custom range (format: 'YYYY-MM-DD')
    - year, month: untuk filter per bulan
    - sentiment: 'Positif', 'Negatif', 'Netral', atau None (semua)
    - top_n: jumlah kata yang akan ditampilkan
    - include_unigrams: include kata tunggal
    - include_bigrams: include 2-word phrases
    - include_trigrams: include 3-word phrases
    - min_frequency: minimal muncul berapa kali
    
    Returns:
    - List of dict: [{"text": "kata", "value": frequency}, ...]
    """
    
    # Ensure stopwords are loaded
    global STOPWORDS
    if not STOPWORDS:
        STOPWORDS = load_stopwords()
        if not STOPWORDS:
            print("⚠️  Warning: No stopwords loaded. Results may contain noise.")
    
    # Fetch articles
    if year and month:
        articles = get_articles_by_month(year, month, sentiment)
    else:
        articles = get_articles_by_date(start_date, end_date, sentiment)
    
    if not articles:
        print("❌ No articles found for the specified criteria.")
        return []
    
    # Print info
    print("\n" + "="*80)
    print("WORD CLOUD GENERATION - Data-Driven Edition")
    print("="*80)
    print(f"Total articles: {len(articles)}")
    
    if year and month:
        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        print(f"Period: {month_names[month]} {year}")
    else:
        print(f"Period: {start_date or 'start'} to {end_date or 'end'}")
    
    print(f"Sentiment filter: {sentiment or 'All'}")
    print(f"Stopwords loaded: {len(STOPWORDS)}")
    print(f"Include: ", end='')
    included = []
    if include_unigrams:
        included.append('unigrams')
    if include_bigrams:
        included.append('bigrams')
    if include_trigrams:
        included.append('trigrams')
    print(', '.join(included))
    print("="*80)
    
    # Combine all content
    all_content = [f"{row.title} {row.content}" for row in articles]
    
    # Calculate term frequencies
    print("\n🔍 Extracting and counting terms...")
    term_frequencies = calculate_term_frequencies(
        all_content,
        include_unigrams=include_unigrams,
        include_bigrams=include_bigrams,
        include_trigrams=include_trigrams
    )
    
    print(f"   Found {len(term_frequencies)} unique terms")
    
    # Filter by frequency
    print(f"\n🔧 Filtering (min_freq={min_frequency})...")
    filtered_terms = filter_by_frequency(
        term_frequencies,
        min_freq=min_frequency,
        max_freq_percentile=95
    )
    
    print(f"   After filtering: {len(filtered_terms)} terms")
    
    # Get top N
    top_terms = filtered_terms.most_common(top_n)
    
    if not top_terms:
        print("\n⚠️  No terms found after filtering!")
        return []
    
    # Format untuk word cloud library (react-wordcloud format)
    wordcloud_data = [
        {
            "text": term,
            "value": freq
        }
        for term, freq in top_terms
    ]
    
    # Print preview
    print(f"\n📊 TOP {min(20, len(wordcloud_data))} TERMS:")
    print(f"   {'Rank':<6} {'Term':<40} {'Frequency':>10}")
    print(f"   {'-'*6} {'-'*40} {'-'*10}")
    for i, item in enumerate(wordcloud_data[:20], 1):
        print(f"   {i:<6} {item['text']:<40} {item['value']:>10,}")
    
    print("="*80 + "\n")
    
    return wordcloud_data


def save_wordcloud_json(data, filename=None, metadata=None):
    """
    Simpan hasil ke JSON file untuk frontend
    
    Parameters:
    - data: wordcloud data
    - filename: custom filename (optional)
    - metadata: additional info to save (optional)
    """
    if not data:
        print("⚠️  No data to save!")
        return None
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wordcloud_{timestamp}.json"
    
    # Ensure .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    output_path = f"/home/claude/{filename}"
    
    # Prepare output
    output = {
        "wordcloud_data": data,
        "metadata": metadata or {},
        "generated_at": datetime.now().isoformat(),
        "total_terms": len(data)
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Data saved to: {output_path}")
    return output_path


# ============================================================================
# API ENDPOINT HELPER (untuk Next.js)
# ============================================================================

def generate_for_api(params):
    """
    Helper function untuk dipanggil dari Next.js API route
    
    Parameters:
    - params: dict with keys:
        - year, month (int)
        - start_date, end_date (str: 'YYYY-MM-DD')
        - sentiment (str: 'Positif'/'Negatif'/'Netral'/None)
        - top_n (int, default: 50)
        - include_unigrams (bool, default: True)
        - include_bigrams (bool, default: True)
        - include_trigrams (bool, default: True)
    
    Returns:
    - dict: {"success": bool, "data": [...], "metadata": {...}}
    """
    try:
        # Load stopwords if not loaded
        global STOPWORDS
        if not STOPWORDS:
            STOPWORDS = load_stopwords()
        
        # Extract params
        year = params.get('year')
        month = params.get('month')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        sentiment = params.get('sentiment')
        top_n = params.get('top_n', 50)
        include_unigrams = params.get('include_unigrams', True)
        include_bigrams = params.get('include_bigrams', True)
        include_trigrams = params.get('include_trigrams', True)
        
        # Generate wordcloud
        data = generate_wordcloud_data(
            start_date=start_date,
            end_date=end_date,
            year=year,
            month=month,
            sentiment=sentiment,
            top_n=top_n,
            include_unigrams=include_unigrams,
            include_bigrams=include_bigrams,
            include_trigrams=include_trigrams
        )
        
        # Metadata
        metadata = {
            "filters": {
                "year": year,
                "month": month,
                "start_date": start_date,
                "end_date": end_date,
                "sentiment": sentiment
            },
            "settings": {
                "top_n": top_n,
                "include_unigrams": include_unigrams,
                "include_bigrams": include_bigrams,
                "include_trigrams": include_trigrams
            }
        }
        
        return {
            "success": True,
            "data": data,
            "metadata": metadata
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": []
        }


# ============================================================================
# MAIN EXECUTION EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("WORD CLOUD GENERATOR V2 - Test Run")
    print("="*80)
    
    # Load stopwords
    STOPWORDS = load_stopwords()
    
    if not STOPWORDS:
        print("\n⚠️  CRITICAL: No stopwords loaded!")
        print("Please run 'python analyze_corpus.py' first to generate stopwords.")
        exit(1)
    
    # Example 1: Word cloud untuk berita Negatif di November 2025
    print("\n" + "="*80)
    print("Example 1: Negative news in November 2025")
    print("="*80)
    data_nov_neg = generate_wordcloud_data(
        year=2025,
        month=11,
        sentiment='Negatif',
        top_n=50,
        include_unigrams=True,
        include_bigrams=True,
        include_trigrams=True
    )
    
    if data_nov_neg:
        save_wordcloud_json(
            data_nov_neg, 
            filename="wordcloud_nov2025_negative.json",
            metadata={
                "period": "November 2025",
                "sentiment": "Negatif",
                "description": "Word cloud untuk isu negatif bulan November 2025"
            }
        )
    
    # Example 2: Word cloud untuk semua sentimen Q4 2025
    print("\n" + "="*80)
    print("Example 2: All sentiment from Oct 1 - Dec 31, 2025")
    print("="*80)
    data_q4 = generate_wordcloud_data(
        start_date='2025-10-01',
        end_date='2025-12-31',
        sentiment=None,  # Semua sentimen
        top_n=60,
        include_unigrams=True,
        include_bigrams=True,
        include_trigrams=False  # Skip trigrams untuk variety
    )
    
    if data_q4:
        save_wordcloud_json(
            data_q4,
            filename="wordcloud_q4_2025_all.json",
            metadata={
                "period": "Q4 2025 (Oct-Dec)",
                "sentiment": "All",
                "description": "Word cloud untuk semua berita Q4 2025"
            }
        )
    
    # Example 3: Word cloud khusus Bigrams & Trigrams (Phrases only)
    print("\n" + "="*80)
    print("Example 3: Bigrams & Trigrams only (December 2025, Negative)")
    print("="*80)
    data_phrases = generate_wordcloud_data(
        year=2025,
        month=12,
        sentiment='Negatif',
        top_n=40,
        include_unigrams=False,  # Hanya phrase
        include_bigrams=True,
        include_trigrams=True
    )
    
    if data_phrases:
        save_wordcloud_json(
            data_phrases,
            filename="wordcloud_dec2025_phrases_only.json",
            metadata={
                "period": "December 2025",
                "sentiment": "Negatif",
                "description": "Word cloud phrases (bigrams & trigrams) untuk isu negatif"
            }
        )
    
    print("\n" + "="*80)
    print("✅ ALL EXAMPLES COMPLETED!")
    print("="*80)
    print("\nGenerated files:")
    print("  1. wordcloud_nov2025_negative.json")
    print("  2. wordcloud_q4_2025_all.json")
    print("  3. wordcloud_dec2025_phrases_only.json")
    print("\nThese JSON files are ready to be consumed by the frontend!")
    print("="*80 + "\n")