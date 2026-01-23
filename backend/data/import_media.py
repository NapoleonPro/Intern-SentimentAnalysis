import pandas as pd
from sqlalchemy import create_engine

# --- KONFIGURASI ---
DB_USER = 'postgres'
DB_PASS = 'admin'  
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'db_pkp_aceh'

# Buat koneksi ke database
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

try:
    # 1. Baca file CSV
    # Pastikan file csv berada di folder yang sama dengan script ini
    df = pd.read_csv('media_mitra.csv')
    
    # 2. Pilih dan Ganti Nama Kolom agar sesuai dengan Tabel Database
    # CSV: Media, Alamat Website, Perusahaan
    # DB: name, domain_url, company
    df_clean = df[['Media', 'Alamat Website', 'Perusahaan']].copy()
    df_clean.columns = ['name', 'domain_url', 'company']
    
    # 3. Masukkan ke Database
    # if_exists='append' artinya tambahkan data ke tabel yang sudah ada
    df_clean.to_sql('media_sources', engine, if_exists='append', index=False)
    
    print("BERHASIL! Data media berhasil masuk ke database.")

except Exception as e:
    print("TERJADI ERROR:")
    print(e)