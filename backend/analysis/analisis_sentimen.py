"""
SENTIMENT ANALYSIS - AI-FOCUSED VERSION
Menggunakan IndoBERT sebagai engine utama dengan minimal rule-based intervention
"""

import os
from sqlalchemy import create_engine, text
from transformers import pipeline
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}')

# Inisialisasi model sekali saja (lebih efisien)
logger.info("Loading IndoBERT model...")
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="w11wo/indonesian-roberta-base-sentiment-classifier",
    truncation=True,
    max_length=512
)
logger.info("Model loaded successfully!")


def get_data():
    """Ambil data artikel dari database"""
    with engine.connect() as conn:
        query = text("""
            SELECT id, title, content 
            FROM articles 
            WHERE content IS NOT NULL 
            ORDER BY published_date DESC
        """)
        return conn.execute(query).fetchall()


def save_result(article_id: int, label: str, score: float, notes: str = ''):
    """Simpan hasil analisis ke database"""
    label_map = {
        'positive': 'Positif',
        'neutral': 'Netral', 
        'negative': 'Negatif'
    }
    final_label = label_map.get(label, 'Netral')
    
    with engine.connect() as conn:
        query = text("""
            UPDATE articles 
            SET sentiment_label = :label, 
                sentiment_score = :score,
                analysis_method = :method,
                analysis_notes = :notes,
                updated_at = NOW()
            WHERE id = :id
        """)
        conn.execute(query, {
            "label": final_label,
            "score": score,
            "method": "IndoBERT",
            "notes": notes,
            "id": article_id
        })
        conn.commit()


def analyze_sentiment(title: str, content: str):
    """
    Analisis sentimen menggunakan IndoBERT
    
    Returns:
        (label, confidence_score, notes)
    """
    # Gabungkan title dan content, prioritaskan title karena biasanya lebih informatif
    full_text = f"{title}. {content}"
    
    # Batasi panjang teks untuk analisis (ambil bagian paling penting)
    # Title + 800 karakter pertama content biasanya sudah cukup representatif
    text_for_analysis = full_text[:1200]
    
    try:
        # Analisis dengan IndoBERT
        result = sentiment_analyzer(text_for_analysis)[0]
        
        label = result['label']
        score = result['score']
        
        # Kategorikan confidence level untuk catatan
        if score >= 0.85:
            conf_note = "Very High Confidence"
        elif score >= 0.70:
            conf_note = "High Confidence"
        elif score >= 0.55:
            conf_note = "Medium Confidence"
        else:
            conf_note = "Low Confidence"
        
        notes = f"{conf_note} - Model: IndoBERT"
        
        return label, score, notes
    
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return 'neutral', 0.5, f"Error: {str(e)}"


def run_analysis():
    """Jalankan analisis sentimen"""
    print("=" * 100)
    print("SENTIMENT ANALYSIS - AI-FOCUSED (IndoBERT)")
    print("=" * 100)
    
    data = get_data()
    total = len(data)
    print(f"\nMenganalisis {total} artikel dengan IndoBERT...\n")
    
    stats = {'positive': 0, 'neutral': 0, 'negative': 0}
    confidence_levels = {'very_high': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    for i, row in enumerate(data, 1):
        article_id, title, content = row
        
        try:
            label, score, notes = analyze_sentiment(title, content)
            
            # Simpan hasil
            save_result(article_id, label, score, notes)
            
            # Update statistik
            stats[label] += 1
            
            # Track confidence distribution
            if score >= 0.85:
                confidence_levels['very_high'] += 1
            elif score >= 0.70:
                confidence_levels['high'] += 1
            elif score >= 0.55:
                confidence_levels['medium'] += 1
            else:
                confidence_levels['low'] += 1
            
            # Display progress
            label_display = label.upper()[:3]
            conf_bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            
            print(f"[{i:4d}/{total}] {label_display:3s} [{conf_bar}] {score:.3f} | {title[:55]}")
            
        except Exception as e:
            logger.error(f"Error processing article {article_id}: {e}")
            save_result(article_id, 'neutral', 0.5, f"Processing error: {str(e)}")
            stats['neutral'] += 1
    
    # Tampilkan ringkasan
    print("\n" + "=" * 100)
    print("RINGKASAN HASIL ANALISIS:")
    print("-" * 100)
    print(f"  Positif  : {stats['positive']:4d} artikel ({stats['positive']/total*100:5.1f}%)")
    print(f"  Netral   : {stats['neutral']:4d} artikel ({stats['neutral']/total*100:5.1f}%)")
    print(f"  Negatif  : {stats['negative']:4d} artikel ({stats['negative']/total*100:5.1f}%)")
    print("-" * 100)
    print("\nDISTRIBUSI CONFIDENCE:")
    print(f"  Very High (≥85%) : {confidence_levels['very_high']:4d} artikel ({confidence_levels['very_high']/total*100:5.1f}%)")
    print(f"  High (70-84%)    : {confidence_levels['high']:4d} artikel ({confidence_levels['high']/total*100:5.1f}%)")
    print(f"  Medium (55-69%)  : {confidence_levels['medium']:4d} artikel ({confidence_levels['medium']/total*100:5.1f}%)")
    print(f"  Low (<55%)       : {confidence_levels['low']:4d} artikel ({confidence_levels['low']/total*100:5.1f}%)")
    print("=" * 100)
    print("\n✓ Semua artikel berhasil dianalisis dengan IndoBERT")
    print("✓ Hasil disimpan di database dengan method: 'IndoBERT'")


if __name__ == "__main__":
    run_analysis()