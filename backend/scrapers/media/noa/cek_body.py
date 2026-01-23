import requests
from bs4 import BeautifulSoup

# Contoh URL berita yang akan dicek.
url = "https://www.noa.co.id/tim-relawan-asn-bpbj-setda-aceh-salurkan-bantuan-masa-panik-untuk-korban-banjir-tamiang/"

try:
    print(f"Sedang mengecek: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Mencari elemen yang berisi konten berita.
    
    candidates = ['entry-content', 'post-content', 'article-content', 'td-post-content', 'content-inner']
    
    found = False
    for class_name in candidates:
        content_div = soup.find('div', class_=class_name)
        if content_div:
            print(f"KETEMU! Isi berita ada di dalam <div class='{class_name}'>")
            
            # Coba ambil paragraf pertama
            paragraphs = content_div.find_all('p')
            if paragraphs:
                print(f"Jumlah Paragraf: {len(paragraphs)}")
                print(f"Cuplikan Awal: {paragraphs[0].get_text()[:100]}...")
            found = True
            break
    
    if not found:
        print("Gagal menebak class isi berita secara otomatis.")

except Exception as e:
    print(e)