import json
import pandas as pd
from app.llm.gemini import generate
from app.tools.serializer import convert_to_serializable

# These are honest message responses from the SQL agent
HONEST_MESSAGES = [
    "not available in the database schema",
    "requested metric is not available",
    "requested data is not available",
]


def _is_honest_message(df: pd.DataFrame) -> bool:
    """
    Detects if the SQL agent returned an honest
    'data not available' message instead of real data.
    """
    if df.empty or len(df.columns) != 1:
        return False

    col = df.columns[0]
    if col.lower() != "message":
        return False

    value = str(df.iloc[0][col]).lower()
    return any(msg in value for msg in HONEST_MESSAGES)


def generate_answer(
    question: str,
    df: pd.DataFrame,
    analysis: dict,
) -> str:
    if df.empty or not analysis.get("has_data"):
        return "No data was found to answer this question."

    # Return honest message directly without LLM
    if _is_honest_message(df):
        return str(df.iloc[0]["message"])

    stats = analysis.get("stats", {})

    # Categorical/grouped data
    if not stats:
        sample = convert_to_serializable(df.head(3).to_dict(orient="records"))
        total_groups = len(df)

        system = """You are a data analyst presenting results to a user.
Summarize the data results clearly and concisely.
Do not invent any numbers or data not shown.
2 to 3 sentences maximum."""

        prompt = f"""Question: {question}

Total groups returned: {total_groups}
Sample of results: {json.dumps(sample, default=str)}

Write a brief summary of these results."""

        return generate(prompt, system)

    # Numeric data
    data_summary = df.head(5).to_string(index=False)
    stats_str = json.dumps(
        convert_to_serializable(stats),
        indent=2
    )

    system = """You are a business data analyst presenting insights to a non-technical manager.

Rules:
- Use ONLY the numbers from the data and statistics provided.
- Never invent or estimate numbers.
- Be concise and business-focused.
- Highlight the most important finding first.
- 2 to 4 sentences maximum.
- If the column names do not match the question exactly, say what data
  was actually used rather than pretending it answers the question."""

    prompt = f"""Business Question: {question}

Query Results:
{data_summary}

Calculated Statistics:
{stats_str}

Write a clear business insight answering this question.
If the data does not fully answer the question, say so clearly."""

    return generate(prompt, system)