from bs4 import BeautifulSoup
import re
import pandas as pd
from tqdm import tqdm


def extract_product_action(card):
    data = {}
    action = card.select_one(".product-action")
    for inp in action.select("input[name^=bit-fbq-]"):
        raw_key = inp.get("name")            
        key = raw_key.split("-")[-1]          
        data[key] = inp.get("value")
    return data


def extract_rating(card):
    rating = 0.0
    for star in card.select(".product-rating .product-review-point .point-rating"):
        classes = star.get("class", [])
        if "point-full" in classes:
            rating += 1
        elif "point-partial" in classes:
            rating += 0.5
            style = star.get("style") or ""
            if "clip-path" in style:
                import re
                m = re.search(r"inset\(0\s+(\d+)%", style)
                if m:
                    right_cut = int(m.group(1))   
                    frac = (100 - right_cut) / 100
                    rating += (frac - 0.5)  
    return rating


def extract_product_price_info(card):
    data = {}
    for child in card.select_one(".product-price-info").find_all(recursive=False):
        data[child.name] = child.get_text(" ", strip=True)
    return data



file_path = "data/html/page_1.html"

with open(file_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

cards = soup.select(".cms-element-product-listing .card.product-box")
rows = []
for i, card in tqdm(enumerate(cards[:2], 1)):
    data = {}
    data.update(extract_product_action(card))
    data.update(extract_product_price_info(card))
    data["rating"] = extract_rating(card)
    rows.append(data)

print(pd.DataFrame(rows))