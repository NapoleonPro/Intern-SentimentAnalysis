from sqlalchemy import create_engine, text
from transformers import pipeline
import torch

# db config
DB_USER = 'postgres'
DB_PASS = 'admin' 
DB_NAME = 'db_pkp_aceh'

# REVISI: Daftar kata pemicu dipersempit
# Hanya fokus pada tekanan/kritik, hindari kata teknis bencana
TRIGGER_WORDS = [
    'desak', 'tuntut', 'kecam', 'kritik', 'tagih', 
    'kecewa', 'sayangkan', 'soroti', 'pertanyakan',
    'protes', 'demo', 'tolak', 'gugat', 'parah'
]

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}')

def get_data():
    with engine.connect() as conn:
        q = text("SELECT id, title, content FROM articles WHERE content IS NOT NULL")
        return conn.execute(q).fetchall()

def save_result(id, label, score):
    label_map = {'positive': 'Positif', 'neutral': 'Netral', 'negative': 'Negatif'}
    final_label = label_map.get(label, 'Netral')
    
    with engine.connect() as conn:
        q = text("UPDATE articles SET sentiment_label = :l, sentiment_score = :s WHERE id = :id")
        conn.execute(q, {"l": final_label, "s": score, "id": id})
        conn.commit()

def run():
    print("Loading model...")
    nlp = pipeline(
        "sentiment-analysis", 
        model="w11wo/indonesian-roberta-base-sentiment-classifier",
        tokenizer="w11wo/indonesian-roberta-base-sentiment-classifier",
        truncation=True,
        max_length=512
    )
    
    data = get_data()
    print(f"Re-analyzing {len(data)} articles...")

    for i, row in enumerate(data):
        id, title, content = row
        text_in = f"{title}. {content}"[:1000]
        
        try:
            # 1. AI Analysis
            res = nlp(text_in)[0]
            lab = res['label']
            sco = res['score']
            
            # 2. Manual Override (Logic Revisi)
            title_lower = title.lower()
            is_forced = False
            
            for trigger in TRIGGER_WORDS:
                if trigger in title_lower:
                    lab = 'negative'
                    sco = 0.99
                    is_forced = True
                    break
            
            save_result(id, lab, sco)
            
            status = lab.upper()
            if is_forced: status += " (FORCED)"
            
            # Print progress biar kelihatan bedanya
            print(f"[{i+1}] {status}: {title[:50]}...")
            
        except Exception as e:
            print(f"Err ID {id}: {e}")

    print("Done.")

if __name__ == "__main__":
    run()