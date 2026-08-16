from app.llm.gemini import generate
from app.tools.schema_tool import get_schema_for_prompt


def generate_sql(question: str) -> str:
    """
    Takes a business question, fetches live schema,
    and returns a MySQL SELECT query.
    """
    schema = get_schema_for_prompt()

    system = """You are an expert MySQL data analyst.
Your job is to convert business questions into correct MySQL SQL queries.

Rules:
- Use ONLY SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, or ALTER.
- Only use tables and columns that exist in the schema provided.
- Use proper MySQL date functions like CURDATE(), DATE_SUB(), QUARTER(), YEAR().
- Use table aliases for readability.
- Return ONLY the SQL query — no explanation, no markdown, no backticks.

IMPORTANT — Honesty rules:
- If the question asks for a metric that cannot be calculated from the schema
  (e.g. profit, cost, margin, discount, tax) — do NOT fake it by renaming
  another column. Instead return this exact SQL:
  SELECT 'The requested metric is not available in the database schema.' AS message

- If the question asks for data from a table or column that does not exist,
  return:
  SELECT 'The requested data is not available in the database schema.' AS message

- Never rename a column to make it look like a metric it is not."""

    prompt = f"""{schema}

Business Question: {question}

Write a MySQL SELECT query to answer this question.
If the required data does not exist in the schema, return the honest message SQL above."""

    sql = generate(prompt, system)

    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(lines[1:-1])

    return sql.strip()