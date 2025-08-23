import requests
from tqdm import trange
import argparse
from bs4 import BeautifulSoup

BASE_URL = "https://www.biermarket.de/bier/deutsches-bier/bayern/?order=lagerbestand&p="
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

def get_full_url(page_index):
    return f"{BASE_URL}{page_index}"


def get_url_content(url):
    sess = requests.Session()
    r = sess.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.prettify()


def download_page_html(page_index, output_dir):
    url = get_full_url(page_index)
    html = get_url_content(url)
    output_path = f"{output_dir}/page_{page_index}.html"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download beer pages")
    parser.add_argument("--start", type=int, help="Start page index", default=1)
    parser.add_argument("--end", type=int, help="End page index", default=24)
    parser.add_argument("--output_dir", type=str, help="Output directory", default="data/html")
    args = parser.parse_args()

    for i in trange(args.start, args.end + 1):
        download_page_html(i, args.output_dir)