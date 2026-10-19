"""
Loads Olist dataset CSV files from data/ directory into the 'olist' Postgres database.
Tables are created from CSV file names without foreign keys.
"""

import os
import glob
import re
import pandas as pd
from sqlalchemy import create_engine, text

# Admin connection used to write data
DB_URL = os.environ.get(
    "OLIST_ADMIN_DB_URL",
    "postgresql://postgres:postgres@localhost:5433/olist"
)
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))

def get_table_name(filepath: str) -> str:
    """
    Transforms file names like 'olist_orders_dataset.csv' into 'orders',
    and 'product_category_name_translation.csv' into 'product_category_name_translation'.
    """
    filename = os.path.basename(filepath)
    name = filename.lower()
    if name.endswith(".csv"):
        name = name[:-4]
    name = re.sub(r"^olist_", "", name)
    name = re.sub(r"_dataset$", "", name)
    return name

def main():
    print(f"Connecting to database: {DB_URL}")
    engine = create_engine(DB_URL)

    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {os.path.abspath(DATA_DIR)}.")
        print("Please download the Olist dataset from Kaggle and place the CSV files in data/.")
        return

    print(f"Found {len(csv_files)} CSV file(s) in {DATA_DIR}:")
    for f in csv_files:
        table_name = get_table_name(f)
        print(f" - {os.path.basename(f)} -> table '{table_name}'")

    for f in csv_files:
        table_name = get_table_name(f)
        print(f"\nLoading '{table_name}' from {os.path.basename(f)}...")
        df = pd.read_csv(f)
        print(f"Read {len(df)} rows. Writing to database...")
        df.to_sql(table_name, engine, if_exists="replace", index=False)

    print("\nVerifying row counts in database:")
    with engine.connect() as conn:
        for f in csv_files:
            table_name = get_table_name(f)
            count = conn.execute(text(f'SELECT count(*) FROM "{table_name}"')).scalar()
            print(f" - {table_name}: {count:,} rows")

    print("\nOlist data loading complete.")

if __name__ == "__main__":
    main()
