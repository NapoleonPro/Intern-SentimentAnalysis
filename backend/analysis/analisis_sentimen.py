import os
from sqlalchemy import create_engine, text
from transformers import pipeline
import re
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'admin')
DB_NAME = os.getenv('DB_NAME', 'db_pkp_aceh')
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}')
NEGATIVE_ISSUES = {
    'korupsi': {
        'contexts': ['kpk', 'rampasan', 'sita', 'jaksa', 'tersangka'],
        'confidence': 0.85,
        'note': 'Berita kasus korupsi'
    },
    'ilegal': {
        'contexts': ['tambang', 'pertambangan', 'illegal', 'penambangan'],
        'confidence': 0.80,
        'note': 'Aktivitas ilegal'
    },
    'inflasi': {
        'contexts': ['tinggi', 'naik', 'melonjak', 'tekan'],
        'confidence': 0.70,
        'note': 'Masalah ekonomi'
    },
    'krisis': {
        'contexts': ['listrik', 'air', 'pangan', 'ekonomi', 'pemadaman'],
        'confidence': 0.75,
        'note': 'Situasi krisis'
    },
}
STRONG_NEGATIVE = {
    'desak': ['keras', 'segera', 'lambat', 'gagal'],
    'kecam': ['keras', 'tajam'],
    'protes': ['massa', 'ratusan', 'warga'],
    'tolak': ['tegas', 'keras', 'massa'],
    'gugat': ['pengadilan', 'hukum'],
    'kecewa': ['sangat', 'banyak', 'warga'],
}
NEUTRAL_DISASTER_CONTEXTS = [
    'peringatan', 'memorial', 'mengenang', 'doa bersama',
    'upacara', 'tabur bunga', 'ziarah', 'napak tilas'
]
POSITIVE_ACTIONS = [
    'tinjau', 'pantau', 'salurkan', 'kirim', 'distribusi',
    'gelar', 'adakan', 'laksanakan', 'percepat', 'prioritas',
    'terima penghargaan', 'terima award', 'apresiasi', 
    'sukses', 'berhasil', 'prestasi', 'inovasi'
]
POSITIVE_OVERRIDES = [
    'tuntaskan', 'tuntas', 'selesai', 'rampung',
    'tegaskan komitmen', 'perkuat', 'tingkatkan'
]
def get_data():
    with engine.connect() as conn:
        q = text("""
            SELECT id, title, content 
            FROM articles 
            WHERE content IS NOT NULL 
            ORDER BY published_date DESC
        """)
        return conn.execute(q).fetchall()
def save_result(id, label, score, method, notes=''):
    label_map = {'positive': 'Positif', 'neutral': 'Netral', 'negative': 'Negatif'}
    final_label = label_map.get(label, 'Netral')
    
    with engine.connect() as conn:
        q = text("""
            UPDATE articles 
            SET sentiment_label = :l, 
                sentiment_score = :s,
                analysis_method = :m,
                analysis_notes = :n,
                updated_at = NOW()
            WHERE id = :id
        """)
        conn.execute(q, {
            "l": final_label, 
            "s": score, 
            "m": method,
            "n": notes,
            "id": id
        })
        conn.commit()
def check_negative_issues(text):
    text_lower = text.lower()
    
    for issue, config in NEGATIVE_ISSUES.items():
        if issue in text_lower:
            context_found = any(ctx in text_lower for ctx in config['contexts'])
            
            if context_found:
                return True, config['confidence'], f"ISU: {config['note']}"
    
    return False, 0.0, None
def check_strong_negative(text):
    text_lower = text.lower()
    
    for keyword, contexts in STRONG_NEGATIVE.items():
        if keyword in text_lower:
            pattern = rf'.{{0,150}}{keyword}.{{0,150}}'
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            
            if matches:
                context = ' '.join(matches)
                context_count = sum(1 for ctx in contexts if ctx in context)
                
                if context_count >= 1:
                    conf = 0.75 + (context_count * 0.05)
                    return True, min(conf, 0.85), f"KRITIK: {keyword}"
    
    return False, 0.0, None
def check_neutral_disaster_memorial(text):
    text_lower = text.lower()
    
    disaster_words = ['tsunami', 'banjir', 'gempa', 'bencana', 'korban']
    has_disaster = any(word in text_lower for word in disaster_words)
    
    if has_disaster:
        has_memorial = any(ctx in text_lower for ctx in NEUTRAL_DISASTER_CONTEXTS)
        if has_memorial:
            return True, "MEMORIAL/PERINGATAN"
    
    return False, None
def check_positive_action(text):
    text_lower = text.lower()
    
    for action in POSITIVE_ACTIONS:
        if action in text_lower:
            return True, 0.70, f"AKSI POSITIF: {action}"
    
    return False, 0.0, None
def check_positive_override(text):
    text_lower = text.lower()
    
    for word in POSITIVE_OVERRIDES:
        if word in text_lower:
            return True, f"OVERRIDE: {word}"
    
    return False, None
def analyze_hybrid(title, content):
    full_text = f"{title} {content}"
    text_in = full_text[:1000]
    
    has_pos_override, pos_note = check_positive_override(full_text)
    if has_pos_override:
        return 'positive', 0.75, f'POSITIVE_OVERRIDE', pos_note
    
    is_memorial, mem_note = check_neutral_disaster_memorial(full_text)
    if is_memorial:
        return 'neutral', 0.65, 'MEMORIAL_NEUTRAL', mem_note
    
    has_neg_issue, neg_conf, neg_note = check_negative_issues(full_text)
    if has_neg_issue and neg_conf >= 0.75:
        return 'negative', neg_conf, 'ISSUE_DETECTED', neg_note
    
    has_kritik, krit_conf, krit_note = check_strong_negative(full_text)
    if has_kritik and krit_conf >= 0.70:
        return 'negative', krit_conf, 'KRITIK_DETECTED', krit_note
    
    try:
        nlp = pipeline(
            "sentiment-analysis", 
            model="w11wo/indonesian-roberta-base-sentiment-classifier",
            truncation=True,
            max_length=512
        )
        
        res = nlp(text_in)[0]
        ai_label = res['label']
        ai_score = res['score']
        
    except Exception as e:
        return 'neutral', 0.5, 'AI_ERROR', str(e)
    
    has_pos_action, pos_conf, pos_note = check_positive_action(full_text)
    
    if ai_score > 0.85:
        method = 'AI_HIGH_CONF'
        notes = f"AI: {ai_label} ({ai_score:.2f})"
        return ai_label, ai_score, method, notes
    
    if has_neg_issue and ai_label != 'positive':
        boosted = max(ai_score, neg_conf)
        return 'negative', boosted, 'ISSUE_BOOST', neg_note
    
    if has_kritik and ai_label in ['neutral', 'negative']:
        boosted = max(ai_score, krit_conf)
        return 'negative', boosted, 'KRITIK_BOOST', krit_note
    
    if has_pos_action and ai_label != 'negative':
        boosted = min(ai_score + 0.15, 0.90)
        final_label = 'positive' if ai_label == 'neutral' else ai_label
        return final_label, boosted, 'POSITIVE_BOOST', pos_note
    
    notes = f"AI: {ai_label} ({ai_score:.2f})"
    return ai_label, ai_score, 'AI_PRIMARY', notes
def run():
    print("=" * 80)
    print("SENTIMENT ANALYSIS v3.0 - CONTEXT-AWARE & UNBIASED")
    print("=" * 80)
    
    data = get_data()
    print(f"\nAnalyzing {len(data)} articles...\n")
    
    stats = {'positive': 0, 'neutral': 0, 'negative': 0}
    
    for i, row in enumerate(data, 1):
        article_id, title, content = row
        
        try:
            label, score, method, notes = analyze_hybrid(title, content)
            
            save_result(article_id, label, score, method, notes)
            
            stats[label] = stats.get(label, 0) + 1
            
            conf = "HIGH" if score > 0.80 else "MED" if score > 0.65 else "LOW"
            label_display = label.upper()[:3]
            
            print(f"[{i:4d}] {label_display:3s} {score:.2f} {conf:4s} | {method:18s} | {title[:40]:40s}")
            if notes and len(notes) < 50:
                print(f"        └─ {notes}")
            
        except Exception as e:
            print(f"[{i:4d}] ERROR: {e}")
            save_result(article_id, 'neutral', 0.5, 'ERROR', str(e))
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    total = len(data)
    print(f"  Positive : {stats['positive']:4d} ({stats['positive']/total*100:5.1f}%)")
    print(f"  Neutral  : {stats['neutral']:4d} ({stats['neutral']/total*100:5.1f}%)")
    print(f"  Negative : {stats['negative']:4d} ({stats['negative']/total*100:5.1f}%)")
    print("=" * 80)
if __name__ == "__main__":
    run()