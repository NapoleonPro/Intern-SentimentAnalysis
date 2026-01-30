from pandas import read_csv  as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
try:
    df = pd.read_csv('media_mitra.csv')
    
    df_clean = df[['Media', 'Alamat Website', 'Perusahaan']].copy()
    df_clean.columns = ['name', 'domain_url', 'company']
    
    df_clean.to_sql('media_sources', engine, if_exists='append', index=False)
    
    print("BERHASIL! Data media berhasil masuk ke database.")
except Exception as e:
    print("TERJADI ERROR:")
    print(e)