import requests
from bs4 import BeautifulSoup

url = "https://www.noa.co.id/?s=oktober+2025"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    print(f"Judul Halaman: {soup.title.string.strip() if soup.title else 'Tidak ada judul'}")
    print("-" * 30)

    links = soup.find_all('a')
    
    count = 0
    for link in links:
        href = link.get('href')
        text = link.get_text(strip=True)
        
        if href and len(text) > 10 and count < 10:
            parent = link.parent.name
            parent_class = link.parent.get('class')
            print(f"Teks: {text[:30]}...")
            print(f"Link: {href}")
            print(f"Parent Tag: <{parent}> class={parent_class}")
            print("-" * 20)
            count += 1

except Exception as e:
    print(e)