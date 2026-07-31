"""
query_tool.py

Takes a plain-English business question, uses an LLM (via LangChain +
Google Gemini) to translate it into a SQL query against a PostgreSQL
database of real Superstore sales orders, executes it safely
(read-only), and prints the result.

Usage:
    python query_tool.py "What were total sales in the West region?"

Setup:
    1. pip install -r requirements.txt
    2. Set your Gemini API key:  export GOOGLE_API_KEY="your-key-here"
       (get a free key at https://aistudio.google.com/app/apikey)
    3. python db_setup.py   (downloads real data & loads Postgres, run once)
    4. python query_tool.py "your question"
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file in this folder, if present

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": os.environ.get("PGPORT", "5432"),
    "dbname": os.environ.get("PGDATABASE", "superstore"),
    "user": os.environ.get("PGUSER", "appuser"),
    "password": os.environ.get("PGPASSWORD", "appuser_pw"),
}

SCHEMA_DESCRIPTION = """
Table: sales   (real order-level Superstore sales data, ~8,400 rows)
Columns:
  - row_id (integer, primary key)
  - order_id (integer)
  - order_date (date)
  - order_priority (text)          e.g. Low, Medium, High, Critical, Not Specified
  - order_quantity (integer)
  - sales (numeric)                order revenue
  - discount (numeric)             fraction, e.g. 0.05 = 5%
  - ship_mode (text)               e.g. Regular Air, Express Air, Delivery Truck
  - profit (numeric)               can be negative
  - unit_price (numeric)
  - shipping_cost (numeric)
  - customer_name (text)
  - province (text)
  - region (text)                  e.g. West, Ontario, Prarie, Atlantic, Quebec,
                                    Yukon, Northwest Territories, Nunavut
  - customer_segment (text)        e.g. Consumer, Corporate, Home Office, Small Business
  - product_category (text)        e.g. Office Supplies, Furniture, Technology
  - product_subcategory (text)
  - product_name (text)
  - product_container (text)
  - product_base_margin (numeric, nullable)
  - ship_date (date)
"""

PROMPT_TEMPLATE = """You are a SQL expert. Given the database schema below and a
user's question in plain English, write a single PostgreSQL SELECT query
that answers it. Only output the raw SQL query, no explanation, no markdown
formatting, no backticks.

Schema:
{schema}

Question: {question}

SQL query:"""


def build_chain():
    """Builds the LangChain prompt -> LLM chain."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    return prompt | llm


def clean_sql(raw_text: str) -> str:
    """Strips markdown fences / stray formatting the model might add."""
    text = raw_text.strip()
    text = text.replace("```sql", "").replace("```", "")
    return text.strip()


def is_safe_select(sql: str) -> bool:
    """
    Guardrail: only allow single, read-only SELECT statements.
    Treats any generated SQL as untrusted before execution.
    """
    lowered = sql.strip().lower()
    if not lowered.startswith("select"):
        return False
    forbidden = ["insert", "update", "delete", "drop", "alter", "create", ";--", "attach"]
    if any(word in lowered for word in forbidden):
        return False
    if sql.count(";") > 1:
        return False
    return True


def run_query(sql: str):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(sql)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return columns, rows


def print_table(columns, rows):
    if not rows:
        print("(no results)")
        return
    widths = [max(len(str(c)), max((len(str(r[i])) for r in rows), default=0)) for i, c in enumerate(columns)]
    header = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
    print(header)
    print("-" * len(header))
    for row in rows:
        print(" | ".join(str(v).ljust(w) for v, w in zip(row, widths)))


def main():
    if len(sys.argv) < 2:
        print('Usage: python query_tool.py "your question here"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set.")
        print('Set it with: export GOOGLE_API_KEY="your-key-here"')
        print("Get a free key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    chain = build_chain()
    result = chain.invoke({"schema": SCHEMA_DESCRIPTION, "question": question})
    sql = clean_sql(result.content)

    print(f"\nGenerated SQL:\n  {sql}\n")

    if not is_safe_select(sql):
        print("Refusing to execute: query did not pass the read-only safety check.")
        sys.exit(1)

    columns, rows = run_query(sql)
    print("Results:")
    print_table(columns, rows)


if __name__ == "__main__":
    main()