import pandas as pd
from app.llm.gemini import generate
from app.tools.schema_tool import get_schema_for_prompt


def validate_and_reflect(
    question: str,
    sql: str,
    df: pd.DataFrame,
    error: str | None = None,
    attempt: int = 1,
) -> dict:
    """
    Reflects on the SQL result and decides if it needs to be rewritten.

    Returns:
    {
        "needs_retry": bool,
        "reason": str,
        "refined_sql": str | None
    }
    """

    # ── Determine what went wrong ────────────────────────────
    if error:
        issue = f"SQL execution failed with error: {error}"
    elif df.empty:
        issue = "SQL executed successfully but returned 0 rows."
    elif df.isnull().all().all():
        issue = "SQL returned rows but all values are NULL."
    else:
        # Result looks good — no retry needed
        return {
            "needs_retry": False,
            "reason": "Result looks correct.",
            "refined_sql": None
        }

    # ── Ask Gemini to rewrite the SQL ───────────────────────
    schema = get_schema_for_prompt()

    system = """You are an expert MySQL SQL debugger.
You are given a business question, a SQL query that failed or returned bad results,
and the database schema.

Your job is to rewrite the SQL to correctly answer the question.

Rules:
- Use ONLY SELECT statements.
- Only use tables and columns that exist in the schema.
- Fix joins, column names, and filters based on the schema.
- Return ONLY the corrected SQL query.
- No explanation, no markdown, no backticks."""

    prompt = f"""{schema}

Business Question: {question}

Previous SQL (attempt {attempt}):
{sql}

Problem detected:
{issue}

Write a corrected MySQL SELECT query."""

    refined_sql = generate(prompt, system)

    # Strip markdown fences if present
    refined_sql = refined_sql.strip()
    if refined_sql.startswith("```"):
        lines = refined_sql.split("\n")
        refined_sql = "\n".join(lines[1:-1])

    return {
        "needs_retry": True,
        "reason": issue,
        "refined_sql": refined_sql.strip()
    }