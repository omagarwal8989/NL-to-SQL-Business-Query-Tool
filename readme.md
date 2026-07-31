# Natural-Language-to-SQL Dashboard Query Tool

Ask business questions in plain English and get real SQL results back — no manual query writing required.

This tool takes a question like *"What were total sales by region?"*, uses an LLM to translate it into a safe, read-only SQL query, runs it against a PostgreSQL database, and returns the results as a formatted table.

## How it works

1. You type a question in plain English.
2. [LangChain](https://www.langchain.com/) + [Google Gemini](https://ai.google.dev/) convert the question into a SQL `SELECT` query, using the database schema as context.
3. A safety guardrail checks the generated SQL — only single, read-only `SELECT` statements are allowed. Anything else (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, multiple statements, etc.) is blocked before it ever reaches the database.
4. The query runs against PostgreSQL and the results are printed as a table.

## Stack

- **LangChain** — prompt orchestration
- **Google Gemini API** (`gemini-2.5-flash`) — natural language → SQL translation
- **PostgreSQL** — data storage and query execution
- **Python** (`psycopg2`, `python-dotenv`)

## Dataset

Real order-level "Superstore Sales" data (~8,400 rows) — customer segments, product categories, regions, sales, profit, discounts, dates, and more.

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure your environment**

Copy `.env.example` to `.env` and fill in your own values:
```bash
cp .env.example .env
```
```
PGHOST=localhost
PGPORT=5432
PGDATABASE=superstore
PGUSER=your_postgres_username
PGPASSWORD=your_postgres_password
GOOGLE_API_KEY=your_gemini_api_key
```

Get a free Gemini API key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

**3. Load the data**

Place `superstoreSales.csv` in the project folder (or let the script download it automatically), then run:
```bash
python db_setup.py
```

**4. Ask a question**
```bash
python query_tool.py "What were total sales by region?"
```

## Example

```
$ python query_tool.py "What were total sales by region?"

Generated SQL:
  SELECT region, SUM(sales) FROM sales GROUP BY region

Results:
region                | sum
------------------------------------
Atlantic              | 2014248.2035
Yukon                 | 975867.3710
Northwest Territories | 800847.3295
Ontario               | 3063212.4795
Prarie                | 2837304.6015
West                  | 3597549.2755
Quebec                | 1510195.0800
Nunavut               | 116376.4835
```

More example questions to try:
```bash
python query_tool.py "What are the top 5 products by profit?"
python query_tool.py "Which customer segment has the highest average discount?"
```

## Safety

All generated SQL is treated as untrusted input. Before execution, queries are checked to ensure they:
- Start with `SELECT`
- Contain no data-modifying or schema-modifying keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`)
- Contain only a single statement (no `;`-separated injection attempts)

Any query that fails these checks is rejected and never runs against the database.

## Possible extensions

- Deploy as a hosted API (e.g. AWS Lambda or EC2) for use in a BI dashboard
- Add a lightweight web frontend for non-technical users
- Support additional databases (MySQL, BigQuery, Snowflake)