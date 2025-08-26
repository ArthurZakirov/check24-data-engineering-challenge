import pandas as pd
import argparse
import re

def extract_euro_as_float(s):
    if pd.isna(s):
        return None
    s = str(s).replace("\xa0", " ")   
    m = re.search(r"\d+[.,]?\d*", s) 
    if not m:
        return None
    num = m.group(0)
    return float(num.replace(",", "."))


def extract_liter(liter_str):
    if pd.isna(liter_str):
        return None
    return float(liter_str.split(" ")[0])


def process_data(df):
    base = df.drop_duplicates(subset=["id"], keep="first")
    return pd.DataFrame({
        "id": base["id"],
        "name": base["name"],
        "price": base["price"],
        "pre_sale_price": base["list-price-price"].apply(extract_euro_as_float),
        "product-deposit": base["product-deposit"].apply(extract_euro_as_float),
        "price-unit-content": base["price-unit-content"].apply(extract_liter),
        "manufacturer": base["manufacturer"],
        "rating": base["rating"]
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="data/csv/raw.csv")
    parser.add_argument("--output-path", default="data/csv/new.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.data_path)
    df = process_data(df)
    df.to_csv(args.output_path, index=False)
