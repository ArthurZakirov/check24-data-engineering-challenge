from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm, trange
import re
from scrape_util import get_full_url, get_url_content
import argparse


def extract_product_action(card: BeautifulSoup) -> dict:
    data = {}
    action = card.select_one(".product-action")
    if not action:
        return data
    for inp in action.select('input[name^="bit-fbq-"]'):
        raw_key = inp.get("name")
        key = raw_key.split("-")[-1]
        key = key.replace("-", "_")
        val = inp.get("value")
        data[key] = val
    return data


def extract_product_price_info(card: BeautifulSoup) -> dict:
    out = {}
    root = card.select_one(".product-price-info")
    if not root:
        return out
    for el in root.find_all():
        cls = el.get("class")
        key = el.name if not cls else cls[0]
        out[key] = el.get_text(" ", strip=True)
    return out


def extract_rating(card: BeautifulSoup) -> float | None:
    rating = 0.0
    stars = card.select(".product-rating .product-review-point .point-rating")
    if not stars:
        return None
    for star in stars:
        classes = star.get("class", [])
        if "point-full" in classes:
            rating += 1.0
        elif "point-partial" in classes:
            frac = 0.5
            style = star.get("style") or ""
            m = re.search(r"inset\(0\s+(\d+)%", style)
            if m:
                right_cut = int(m.group(1))
                frac = (100 - right_cut) / 100.0
            rating += frac
    return rating


def extract_manufacturer(card: BeautifulSoup) -> str | None:
    href = card.select_one("a.product-name").get("href")
    soup = get_url_content(href)
    table = soup.select_one("table.product-detail-properties-table")
    tr = table.select_one("tr")
    tds = tr.find_all("td")
    text = tds[0].get_text(strip=True)
    manufacturer = text.split(":")[1]
    return manufacturer


def extract_page_data(soup: BeautifulSoup) -> pd.DataFrame:
    cards = soup.select(".cms-element-product-listing .card.product-box")
    rows = []
    for card in tqdm(cards, total=len(cards), desc="Products", leave=False):
        row = {}
        row.update(extract_product_action(card))
        row.update(extract_product_price_info(card))
        row["rating"] = extract_rating(card)
        row["manufacturer"] = extract_manufacturer(card)
        rows.append(row)
    return pd.DataFrame(rows)


def extract_bavaria_data(start: int, end: int) -> pd.DataFrame:
    dfs = []
    for page_idx in trange(start, end + 1, desc="Pages", leave=True):
        url = get_full_url(page_idx)
        html = get_url_content(url)
        df = extract_page_data(html)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True, axis=0)


def parse_command_line_args():
    parser = argparse.ArgumentParser(description="Download beer pages")
    parser.add_argument("--start", type=int, help="Start page index", default=1)
    parser.add_argument("--end", type=int, help="End page index", default=24)
    parser.add_argument(
        "--output_path", type=str, help="Output path", default="data/bavaria.csv"
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_command_line_args()
    df = extract_bavaria_data(args.start, args.end)
    df.to_csv(args.output_path, index=False)
