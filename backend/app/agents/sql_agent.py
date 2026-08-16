from app.llm.gemini import generate
from app.tools.schema_tool import get_schema_for_prompt


def generate_sql(question: str, plan: dict) -> str:
    """
    Takes a business question and analysis plan,
    returns a MySQL SELECT query based on the live database schema.
    """
    schema = get_schema_for_prompt()
    system = """You are an expert MySQL data analyst.
Your job is to convert business questions into correct MySQL SQL queries.
Rules:
- Use ONLY SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, or ALTER.
- Only use table and column names that exist in the schema provided.
- Use proper MySQL date functions like CURDATE(), DATE_SUB(), QUARTER(), YEAR().
- Use table aliases for readability.
- Return ONLY the SQL query — no explanation, no markdown, no backticks."""
    prompt = f"""{schema}
ANALYSIS PLAN:
Goal: {plan['goal']}
Steps: {', '.join(plan['steps'])}

Business Question: {question}

Write a MySQL SELECT query to answer this question."""

    sql = generate(prompt, system)

    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(lines[1:-1])

    return sql.strip()