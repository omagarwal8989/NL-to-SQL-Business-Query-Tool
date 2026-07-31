# NL-to-SQL Business Query Tool

A tool that turns a plain-English business question into a SQL query,
runs it against a real dataset in PostgreSQL, and returns the answer —
built to demonstrate AI-assisted query generation for BI/reporting use cases.

## Dataset

Uses the real **Sample Superstore Sales** dataset (~8,400 real orders):
region, product category/subcategory, customer segment, sales, profit,
discount, ship mode, dates, and more.
Source: https://github.com/curran/data (superstoreSales.csv)

## Example

```
$ python query_tool.py "What were total sales by region?"

Generated SQL:
  SELECT region, ROUND(SUM(sales)::numeric, 2) as total_sales
  FROM sales GROUP BY region ORDER BY total_sales DESC;

Results:
region                | total_sales
-----------------------------------
West                  | 3597549.28
Ontario               | 3063212.48
Prarie                | 2837304.60
...
```

```
$ python query_tool.py "Which product category is most profitable?"

Generated SQL:
  SELECT product_category, ROUND(SUM(profit)::numeric, 2) as total_profit
  FROM sales GROUP BY product_category ORDER BY total_profit DESC LIMIT 1;

Results:
product_category | total_profit
-------------------------------
Technology       | 886313.52
```

## How it works

1. `db_setup.py` downloads the real Superstore CSV, cleans known quirks
   in the source file (old-Mac-style `\r` line endings, stray blank rows),
   and loads it into a PostgreSQL table (`sales`).
2. `query_tool.py` takes a question, sends the database schema + question
   to Gemini (via LangChain) to generate a PostgreSQL query.
3. Before running anything, the query passes through a **safety check**
   that only allows single, read-only `SELECT` statements — any
   `INSERT`/`UPDATE`/`DELETE`/`DROP`/chained statement is rejected. LLM
   output is treated as untrusted input, not executed blindly.
4. The query runs against Postgres and results print as a formatted table.

## Setup

Requires a running PostgreSQL instance (local install, or a hosted free
tier like Neon/Supabase).

```bash
pip install -r requirements.txt

# Set your Postgres connection (defaults shown — edit as needed)
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=superstore
export PGUSER=appuser
export PGPASSWORD=appuser_pw

python db_setup.py                       # downloads real data & loads Postgres (run once)

export GOOGLE_API_KEY="your-key-here"    # free key: https://aistudio.google.com/app/apikey
python query_tool.py "your question here"
```

If you're setting up Postgres locally for the first time:

```bash
sudo apt-get install -y postgresql postgresql-contrib
sudo service postgresql start
sudo -u postgres psql -c "CREATE USER appuser WITH PASSWORD 'appuser_pw';"
sudo -u postgres psql -c "CREATE DATABASE superstore OWNER appuser;"
```

## Tech stack

Python, LangChain, Google Gemini API, PostgreSQL

## Possible extensions

- Add a simple web UI (Streamlit/FastAPI) instead of CLI
- Deploy as an AWS Lambda function behind API Gateway for on-demand queries,
  with the Postgres instance on RDS