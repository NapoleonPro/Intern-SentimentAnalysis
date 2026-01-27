import pandas as pd
from sqlalchemy import create_engine
DB_USER = 'postgres'
DB_PASS = 'admin'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'db_pkp_aceh'
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