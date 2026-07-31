# """
# db_setup.py

# Downloads the real "Sample Superstore Sales" dataset (~8,400 real orders:
# region, product category, sales, profit, customer segment, dates, etc.)
# and loads it into a local PostgreSQL database, so the NL-to-SQL tool has
# real, messy, realistic data to query against.

# Source dataset: https://github.com/curran/data (superstoreSales.csv)

# Run this once before using query_tool.py.

# Requires a running PostgreSQL instance. Set connection details via env
# vars, or edit the defaults below:
#     PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
# """

# import os
# import io
# import urllib.request
# import psycopg2
# from dotenv import load_dotenv

# load_dotenv()  # reads variables from a .env file in this folder, if present

# CSV_URL = "https://raw.githubusercontent.com/curran/data/gh-pages/superstoreSales/superstoreSales.csv"

# DB_CONFIG = {
#     "host": os.environ.get("PGHOST", "localhost"),
#     "port": os.environ.get("PGPORT", "5432"),
#     "dbname": os.environ.get("PGDATABASE", "superstore"),
#     "user": os.environ.get("PGUSER", "appuser"),
#     "password": os.environ.get("PGPASSWORD", "appuser_pw"),
# }

# SCHEMA_SQL = """
# DROP TABLE IF EXISTS sales;
# CREATE TABLE sales (
#     row_id INTEGER PRIMARY KEY,
#     order_id INTEGER,
#     order_date DATE,
#     order_priority TEXT,
#     order_quantity INTEGER,
#     sales NUMERIC,
#     discount NUMERIC,
#     ship_mode TEXT,
#     profit NUMERIC,
#     unit_price NUMERIC,
#     shipping_cost NUMERIC,
#     customer_name TEXT,
#     province TEXT,
#     region TEXT,
#     customer_segment TEXT,
#     product_category TEXT,
#     product_subcategory TEXT,
#     product_name TEXT,
#     product_container TEXT,
#     product_base_margin NUMERIC,
#     ship_date DATE
# );
# """


# def download_and_clean_csv() -> str:
#     """
#     Downloads the raw CSV and fixes known quirks in the source file:
#     - it uses old-Mac-style \\r line endings instead of \\n
#     - it has stray blank rows
#     """
#     print("Downloading dataset...")
#     with urllib.request.urlopen(CSV_URL) as resp:
#         raw_bytes = resp.read()

#     # Source file is Latin-1 encoded with \r line endings
#     text = raw_bytes.decode("latin-1").replace("\r", "\n")
#     lines = [line for line in text.split("\n") if line.strip()]
#     return "\n".join(lines)


# def load_into_postgres(csv_text: str):
#     conn = psycopg2.connect(**DB_CONFIG)
#     cur = conn.cursor()

#     print("Creating table...")
#     cur.execute(SCHEMA_SQL)

#     print("Loading rows...")
#     buf = io.StringIO(csv_text)
#     cur.copy_expert(
#         "COPY sales FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')",
#         buf,
#     )

#     conn.commit()
#     cur.execute("SELECT COUNT(*) FROM sales")
#     count = cur.fetchone()[0]
#     print(f"Loaded {count} rows into 'sales' table in database '{DB_CONFIG['dbname']}'")

#     cur.close()
#     conn.close()


# if __name__ == "__main__":
#     csv_text = download_and_clean_csv()
#     load_into_postgres(csv_text)








"""
db_setup.py

Loads the "Sample Superstore Sales" dataset (~8,400 real orders:
region, product category, sales, profit, customer segment, dates, etc.)
into a local PostgreSQL database, so the NL-to-SQL tool has real,
messy, realistic data to query against.

Looks for a local file first:
    superstoreSales.csv   (put this in the same folder as this script)

If it's not found, falls back to downloading it from:
    https://github.com/curran/data (superstoreSales.csv)

Run this once before using query_tool.py.

Requires a running PostgreSQL instance. Set connection details via env
vars (or a .env file), or edit the defaults below:
    PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
"""

import os
import io
import urllib.request
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file in this folder, if present

CSV_URL = "https://raw.githubusercontent.com/curran/data/gh-pages/superstoreSales/superstoreSales.csv"
LOCAL_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "superstoreSales.csv")

DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": os.environ.get("PGPORT", "5432"),
    "dbname": os.environ.get("PGDATABASE", "superstore"),
    "user": os.environ.get("PGUSER", "appuser"),
    "password": os.environ.get("PGPASSWORD", "appuser_pw"),
}

SCHEMA_SQL = """
DROP TABLE IF EXISTS sales;
CREATE TABLE sales (
    row_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    order_date DATE,
    order_priority TEXT,
    order_quantity INTEGER,
    sales NUMERIC,
    discount NUMERIC,
    ship_mode TEXT,
    profit NUMERIC,
    unit_price NUMERIC,
    shipping_cost NUMERIC,
    customer_name TEXT,
    province TEXT,
    region TEXT,
    customer_segment TEXT,
    product_category TEXT,
    product_subcategory TEXT,
    product_name TEXT,
    product_container TEXT,
    product_base_margin NUMERIC,
    ship_date DATE
);
"""


def get_csv_text() -> str:
    """
    Returns the CSV content as a cleaned string.
    Uses the local file if present, otherwise downloads it.
    Either way, fixes known quirks in the source data:
    - old-Mac-style \\r line endings instead of \\n
    - stray blank rows
    - Latin-1 encoding
    """
    if os.path.exists(LOCAL_CSV_PATH):
        print(f"Found local file: {LOCAL_CSV_PATH}")
        with open(LOCAL_CSV_PATH, "rb") as f:
            raw_bytes = f.read()
    else:
        print("No local superstoreSales.csv found — downloading instead...")
        with urllib.request.urlopen(CSV_URL) as resp:
            raw_bytes = resp.read()

    # Source file is Latin-1 encoded with \r line endings
    text = raw_bytes.decode("latin-1").replace("\r", "\n")
    lines = [line for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def load_into_postgres(csv_text: str):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("Creating table...")
    cur.execute(SCHEMA_SQL)

    # Source CSV uses US-style month/day/year dates (e.g. 10/13/2010) —
    # tell Postgres to parse them that way instead of day/month/year.
    cur.execute("SET DateStyle = 'MDY';")

    print("Loading rows...")

    buf = io.StringIO(csv_text)
    cur.copy_expert(
        "COPY sales FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')",
        buf,
    )

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM sales")
    count = cur.fetchone()[0]
    print(f"Loaded {count} rows into 'sales' table in database '{DB_CONFIG['dbname']}'")

    cur.close()
    conn.close()


if __name__ == "__main__":
    csv_text = get_csv_text()
    load_into_postgres(csv_text)