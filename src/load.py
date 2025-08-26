import pandas as pd
import sqlite3
import argparse

def run_load_pipeline(csv_path, db_path, table_name):
    df = pd.read_csv(csv_path)
    con = sqlite3.connect(db_path)
    df.to_sql(table_name, con, if_exists="replace", index=False)

    con.commit()
    con.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-path", default="data/csv/processed.csv")
    parser.add_argument("--db-path", default="beer.db")
    parser.add_argument("--table-name", default="beers")
    args = parser.parse_args()

    run_load_pipeline(
        csv_path=args.csv_path,
        db_path=args.db_path,
        table_name=args.table_name
    )
