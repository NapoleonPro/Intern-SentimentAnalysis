from sqlalchemy import create_engine, text
from transformers import pipeline
import torch

# DB config
DB_USER = 'postgres'
DB_PASS = 'admin' 
DB_NAME = 'db_pkp_aceh'

# Connect DB
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}')

def get_data():
    # fetch unprocessed articles
    with engine.connect() as conn:
        q = text("SELECT id, title, content FROM articles WHERE sentiment_label IS NULL AND content IS NOT NULL")
        return conn.execute(q).fetchall()

def save_result(id, label, score):
    # map to indo
    l_map = {'positive': 'Positif', 'neutral': 'Netral', 'negative': 'Negatif'}
    final_label = l_map.get(label, 'Netral')
    
    # update row
    with engine.connect() as conn:
        q = text("UPDATE articles SET sentiment_label = :l, sentiment_score = :s WHERE id = :id")
        conn.execute(q, {"l": final_label, "s": score, "id": id})
        conn.commit()

def run():
    print("Loading model...")
    # IndoBERT sentiment model
    nlp = pipeline(
        "sentiment-analysis", 
        model="w11wo/indonesian-roberta-base-sentiment-classifier",
        tokenizer="w11wo/indonesian-roberta-base-sentiment-classifier",
        truncation=True,
        max_length=512
    )
    
    data = get_data()
    total = len(data)
    print(f"Processing {total} articles...")

    neg_count = 0
    
    for i, row in enumerate(data):
        id, title, content = row
        
        # combine title + start of content for context
        text_in = f"{title}. {content}"[:1000]
        
        try:
            res = nlp(text_in)[0]
            lab = res['label']
            sco = res['score']
            
            save_result(id, lab, sco)
            
            if lab == 'negative': neg_count += 1
            
            print(f"[{i+1}/{total}] {lab.upper()}: {title[:30]}...")
            
        except Exception as e:
            print(f"Err ID {id}: {e}")

    print("-" * 30)
    print(f"Done. Negatives found: {neg_count}")

if __name__ == "__main__":
    run()