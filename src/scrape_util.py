import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.biermarket.de/bier/deutsches-bier/bayern/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Referer": BASE_URL,
}

def get_full_url(page_index):
    return f"{BASE_URL}?order=lagerbestand&p={page_index}"

def get_url_content(url: str, session: requests.Session | None = None) -> BeautifulSoup:
    s = session or requests.Session()
    r = s.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")