# QueryMind 🤖

An agentic AI system that converts natural language business questions into SQL queries, executes them against your database, and returns data insights, statistics, and visualizations — all in real time.

Built with Python, FastAPI, Google Gemini, and Pandas. Supports MySQL, PostgreSQL, and SQLite.

---

## Table of Contents

- [Demo](#demo)
- [Architecture](#architecture)
- [Agent Pipeline](#agent-pipeline)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [SQL Safety](#sql-safety)
- [Reflection Mechanism](#reflection-mechanism)
- [Database Support](#database-support)
- [Example Questions](#example-questions)
- [Production Considerations](#production-considerations)
- [Docker](#docker)

---

## Demo

```bash
$ query-mind "which artist generated the most revenue?"

  [DONE] Step 0 — Planner
  [DONE] Step 1 — fetch_schema
  [DONE] Step 2 — generate_sql
           SQL: SELECT ar.Name, SUM(il.UnitPrice * il.Quantity) AS Revenue...
  [DONE] Step 3 — validate_sql
  [DONE] Step 4 — execute_sql
           Rows returned: 1
  [DONE] Step 5 — analyze_results
  [DONE] Step 7 — generate_answer

  ────────────────────────────────────────────────────────────
  RESULT
  ────────────────────────────────────────────────────────────

  Answer: Iron Maiden generated the highest revenue at $138.60,
  making them the top earning artist in the database.

  Rows returned: 1
  Execution time: 312ms
```

---

## Architecture

```
User Question
      │
      ▼
┌─────────────────┐
│    Planner      │  Decides pipeline steps and visualization needs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Schema Tool    │  Reads live database structure automatically
│                 │  Works with MySQL / PostgreSQL / SQLite
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQL Agent     │  Generates SQL query using Gemini
│                 │  Uses live schema — never guesses column names
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQL Safety     │  Blocks dangerous queries before execution
│  Validator      │  Rejects INSERT, UPDATE, DELETE, DROP, ALTER
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Database      │────▶│   Reflection    │  If result is wrong or empty
│   Executor      │     │   Agent         │  rewrites SQL and retries (max 3)
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Analyst       │  Calculates stats with Python/Pandas (no LLM)
│   Agent         │  Groups data intelligently based on question intent
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Chart Agent   │  Decides best chart type using Gemini
│                 │  Renders with Plotly
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Answer Agent  │  Generates business-focused answer using Gemini
│                 │  Uses only real data — never invents numbers
└────────┬────────┘
         │
         ▼
    Final Result
```

---

## Agent Pipeline

### Agent 1 — Planner
- Input: Business question
- Output: Execution plan with steps and tools
- LLM used: Yes — one yes/no call to decide if visualization is needed
- Purpose: Decides which agents to run and in what order

### Agent 2 — Schema Tool
- Input: Database connection from `.env`
- Output: Live `CREATE TABLE` statements for all tables
- LLM used: No — pure database inspection
- Purpose: Gives SQL agent accurate table and column names

### Agent 3 — SQL Agent
- Input: Question + live schema
- Output: MySQL / PostgreSQL / SQLite SELECT query
- LLM used: Yes — Gemini generates the SQL
- Purpose: Converts natural language to accurate SQL

### Agent 4 — SQL Safety Validator
- Input: Generated SQL
- Output: Safe / Blocked decision
- LLM used: No — deterministic keyword matching
- Purpose: Prevents dangerous queries from reaching the database

### Agent 5 — Database Executor
- Input: Validated SQL
- Output: Pandas DataFrame with results
- LLM used: No — direct database execution
- Purpose: Runs the query and returns raw data

### Agent 6 — Reflection Agent
- Input: Question + SQL + result (empty or error)
- Output: Refined SQL if needed
- LLM used: Yes — only when result is wrong or empty
- Purpose: Detects bad results and rewrites SQL (max 3 attempts)

### Agent 7 — Analyst Agent
- Input: Raw DataFrame
- Output: Statistics + grouped data
- LLM used: Yes — one yes/no call to decide grouping
- Purpose: Calculates totals, averages, max, min, median with Python. Groups results when appropriate.

### Agent 8 — Chart Agent
- Input: Question + DataFrame
- Output: Chart specification + Plotly JSON
- LLM used: Yes — decides chart type
- Purpose: Selects best visualization and renders it

### Agent 9 — Answer Agent
- Input: Question + DataFrame + statistics
- Output: Business-focused natural language answer
- LLM used: Yes — Gemini writes the answer
- Purpose: Explains results in plain English using only real data

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| API Framework | FastAPI |
| AI Model | Google Gemini 2.0 Flash |
| AI SDK | Google GenAI Python SDK |
| Data Processing | Pandas |
| Visualization | Plotly |
| Database — MySQL | mysql-connector-python |
| Database — PostgreSQL | psycopg2-binary |
| Database — SQLite | Built-in sqlite3 |
| Real-time Streaming | Server-Sent Events (SSE) |
| Config | python-dotenv |
| Validation | Pydantic |
| Server | Uvicorn |

---

## Project Structure

```
Query-Mind/
│
├── app/
│   ├── main.py                    # FastAPI app and all endpoints
│   ├── config.py                  # Environment config
│   │
│   ├── agents/
│   │   ├── planner.py             # Decides pipeline steps
│   │   ├── sql_agent.py           # Generates SQL with Gemini
│   │   ├── validator.py           # Reflects on bad results, rewrites SQL
│   │   ├── analyst.py             # Calculates stats, groups data
│   │   ├── chart_agent.py         # Decides and renders charts
│   │   └── answer_agent.py        # Generates final business answer
│   │
│   ├── tools/
│   │   ├── base_db.py             # Abstract base class for all DB tools
│   │   ├── db_factory.py          # Returns correct DB tool from .env
│   │   ├── mysql_tool.py          # MySQL implementation
│   │   ├── sqlite_tool.py         # SQLite implementation
│   │   ├── postgres_tool.py       # PostgreSQL implementation
│   │   ├── schema_tool.py         # Fetches live schema for prompts
│   │   ├── sql_safety.py          # Blocks dangerous SQL + filters sensitive columns
│   │   ├── chart_tool.py          # Renders Plotly charts
│   │   └── serializer.py          # Converts numpy/pandas types to JSON
│   │
│   ├── llm/
│   │   └── gemini.py              # Single shared Gemini client
│   │
│   └── workflow/
│       └── analyst_workflow.py    # Full pipeline — streaming and non-streaming
│
├── cli.py                         # Terminal interface
├── setup.py                       # Registers query-mind CLI command
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourname/Query-Mind.git
cd Query-Mind
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install CLI command

```bash
pip install -e .
```

### 5. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials — see [Configuration](#configuration) below.

### 6. Run the API server

```bash
uvicorn app.main:app --reload
```

API is available at: `http://localhost:8000`
Swagger docs at: `http://localhost:8000/docs`

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```env
# Google Gemini API key
# Get yours free at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Database type — choose one: mysql | postgres | sqlite
DB_TYPE=mysql

# MySQL (fill if DB_TYPE=mysql)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=your_database_name
MYSQL_USER=your_read_only_user
MYSQL_PASSWORD=your_password

# PostgreSQL (fill if DB_TYPE=postgres)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database_name
POSTGRES_USER=your_read_only_user
POSTGRES_PASSWORD=your_password

# SQLite (fill if DB_TYPE=sqlite)
SQLITE_PATH=./database.db
```

### Important — Use a read-only database user

Never connect with a root or admin account. Create a dedicated read-only user:

```sql
-- MySQL
CREATE USER 'analyst_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT, SHOW VIEW ON your_database.* TO 'analyst_user'@'localhost';
FLUSH PRIVILEGES;

-- PostgreSQL
CREATE USER analyst_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE your_database TO analyst_user;
GRANT USAGE ON SCHEMA public TO analyst_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst_user;
```

---

## Usage

### API Server

Start the server:

```bash
uvicorn app.main:app --reload
```

### Terminal — Single question

```bash
query-mind "which genre has the most tracks?"
```

### Terminal — Interactive mode

```bash
query-mind --interactive
query-mind -i
```

### Terminal — Help

```bash
query-mind --help
```

### HTML Test Page

Open `test_stream.html` in your browser to test the SSE stream visually with a simple UI.

---

## API Documentation

Full Swagger UI available at `http://localhost:8000/docs`

### Main Endpoints

#### `POST /api/stream` — Real-time SSE stream (production)

Streams each agent step as it happens using Server-Sent Events.

```bash
curl -X POST http://localhost:8000/api/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "which artist generated the most revenue?"}' \
  --no-buffer
```

Each event is a JSON object:

```
data: {"type": "step", "step": 1, "name": "fetch_schema", "status": "running"}
data: {"type": "step", "step": 1, "name": "fetch_schema", "status": "done"}
data: {"type": "step", "step": 2, "name": "generate_sql", "status": "done", "sql": "SELECT..."}
data: {"type": "final", "answer": "...", "data": [...], "chart": {...}}
data: {"type": "done"}
```

#### `POST /api/analyze` — Single response (testing)

Runs the full pipeline and returns the complete result at once.

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "how many artists are in the database?"}'
```

### Individual Agent Endpoints (debugging)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/agents/planner` | Run planner only |
| GET | `/api/agents/schema` | View live database schema |
| POST | `/api/agents/sql` | Generate SQL only |
| POST | `/api/agents/safety` | Check SQL safety |
| POST | `/api/agents/execute` | Execute SQL |
| POST | `/api/agents/analyst` | Run analyst on data |
| POST | `/api/agents/chart` | Generate chart |
| POST | `/api/agents/answer` | Generate answer |
| POST | `/api/agents/reflection` | Reflect on bad SQL |

### Frontend SSE Integration

```javascript
fetch('http://localhost:8000/api/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: "which artist has the most tracks?" })
}).then(response => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    function read() {
        reader.read().then(({ done, value }) => {
            if (done) return
            const lines = decoder.decode(value).split('\n')
            lines.forEach(line => {
                if (!line.startsWith('data: ')) return
                const data = JSON.parse(line.slice(6))

                if (data.type === 'step') {
                    console.log(`Step ${data.step} — ${data.name}: ${data.status}`)
                }
                if (data.type === 'final') {
                    console.log('Answer:', data.answer)
                    console.log('Data:', data.data)
                }
            })
            read()
        })
    }
    read()
})
```

---

## SQL Safety

The SQL Safety Validator runs before every query reaches the database.

### Blocked operations

```
INSERT    UPDATE    DELETE    DROP
ALTER     TRUNCATE  CREATE    RENAME
GRANT     REVOKE    EXEC      LOAD
OUTFILE   INFILE
```

### Multi-statement detection

Queries with multiple statements separated by `;` are blocked.

### Sensitive column filtering

Even if SQL selects sensitive columns, they are automatically removed from results:

```
password    passwd      secret      token
api_key     api_secret  ssn         credit_card
salary      bank_account            passport
```

### Read-only enforcement

Only `SELECT` and `WITH` (CTE) queries are allowed through.

---

## Reflection Mechanism

The Reflection Agent runs automatically when SQL returns bad results.

```
SQL executes
     │
     ▼
Result empty or all NULL?
     │
     ├── No  → Continue pipeline
     │
     └── Yes → Reflection Agent
                    │
                    ▼
               Gemini rewrites SQL
                    │
                    ▼
               Safety check again
                    │
                    ▼
               Execute again
                    │
                    ▼
               Max 3 attempts
```

The reflection agent receives:
- The original question
- The SQL that failed
- The error or empty result
- The live database schema

It rewrites the SQL to fix joins, column names, filters, and date ranges.

---

## Database Support

The system uses a factory pattern — only change `DB_TYPE` in `.env`:

```
DB_TYPE=mysql     → uses MySQLTool
DB_TYPE=postgres  → uses PostgresTool
DB_TYPE=sqlite    → uses SQLiteTool
```

All three implement the same interface:

```python
get_schema() → str          # returns CREATE TABLE statements
execute_query(sql) → dict   # returns DataFrame + metadata
```

No code changes needed when switching databases.

---

## Example Questions

### Simple lookups
```
How many artists are in the database?
List all music genres
What are the top 10 most expensive tracks?
```

### Aggregations
```
Which artist generated the most revenue?
What is the total revenue from all sales?
Which country has the most customers?
```

### Grouped results
```
Give me 5 tracks for each artist
List albums grouped by artist
Show me all genres with their track counts
```

### Trend analysis
```
Show me total sales revenue per country with a chart
Which genre has the most tracks and show a comparison chart
What are the top 5 best selling tracks of all time?
```

### Complex joins
```
Which customer spent the most money and which country are they from?
Show me employees and how many customers they support
Which invoice has the most line items?
```

---

## Production Considerations

### Security
- Always use a read-only database user
- Never commit `.env` to Git
- SQL safety validator runs on every query
- Sensitive columns are filtered from all results
- Database credentials are never sent to Gemini

### Performance
- Schema is fetched fresh per request — consider caching for large schemas
- `MAX_ROWS = 1000` limits result size — adjust in `config.py`
- `QUERY_TIMEOUT = 30` seconds — adjust based on your database size
- Gemini is called 2-4 times per request — monitor API usage

### Reliability
- Reflection agent retries failed SQL up to 3 times
- All database connections are closed after each query
- `buffered=True` prevents unread result errors in MySQL
- All numpy/pandas types are serialized before returning

### Scaling
- Run multiple uvicorn workers: `uvicorn app.main:app --workers 4`
- SSE connections are stateless — safe to load balance
- Each request creates a new database connection — use a connection pool for high traffic

---

## Docker

Run the full stack with Docker — no local Python setup needed.

### Files

```
Query-Mind/
├── Dockerfile              # builds the API image
├── docker-compose.yml      # runs API + MySQL + PostgreSQL
└── .dockerignore           # excludes venv, .env, cache
```

### Quick start — MySQL with Docker

**Step 1** — Set your `.env`:

```env
GEMINI_API_KEY=your_key_here
DB_TYPE=mysql
MYSQL_HOST=mysql           # use service name, not localhost
MYSQL_PORT=3306
MYSQL_DATABASE=sales_db
MYSQL_USER=analyst_user
MYSQL_PASSWORD=analyst123
```

**Step 2** — Build and start:

```bash
docker compose up --build
```

**Step 3** — API is available at:

```
http://localhost:8000
http://localhost:8000/docs
```

---

### Quick start — External database (your own MySQL/PostgreSQL)

If you already have a database running outside Docker, set `MYSQL_HOST` to your actual host IP instead of the service name:

```env
DB_TYPE=mysql
MYSQL_HOST=192.168.1.100    # your actual DB host
MYSQL_PORT=3306
MYSQL_DATABASE=your_db
MYSQL_USER=analyst_user
MYSQL_PASSWORD=your_password
```

Then run only the API container — skip the database services:

```bash
docker compose up api --build
```

---

### Quick start — SQLite

SQLite needs no database service. Just set `DB_TYPE=sqlite` and mount the file:

```env
DB_TYPE=sqlite
SQLITE_PATH=/app/database.db
```

```bash
docker compose up api --build
```

The `database.db` file in your project root is automatically mounted into the container.

---

### Useful Docker commands

```bash
# Start everything
docker compose up --build

# Start in background
docker compose up -d --build

# View logs
docker compose logs -f api

# Stop everything
docker compose down

# Stop and remove volumes (deletes DB data)
docker compose down -v

# Rebuild after code changes
docker compose up --build api

# Open a shell inside the container
docker exec -it query-mind-api bash

# Run CLI inside container
docker exec -it query-mind-api query-mind "how many artists?"
```

---

### Port reference

| Service | Internal port | External port |
|---------|--------------|---------------|
| API | 8000 | 8000 |
| MySQL | 3306 | 3307 |
| PostgreSQL | 5432 | 5433 |

MySQL and PostgreSQL are exposed on different external ports to avoid conflicts with any local database you already have running.

---

## License

MIT License — free to use, modify, and distribute.

---

## Author

Built as a portfolio project demonstrating practical agentic AI engineering with Python, FastAPI, and Google Gemini.
```
