import json
import pandas as pd
from app.llm.gemini import generate


def generate_answer(
    question: str,
    df: pd.DataFrame,
    analysis: dict,
) -> str:
    """
    Generates a business-focused natural language answer.
    Uses only real data — never invents numbers.
    """
    if df.empty or not analysis.get("has_data"):
        return "No data was found to answer this question."

    data_summary = df.head(5).to_string(index=False)
    stats_str = json.dumps(analysis.get("stats", {}), default=str, indent=2)

    system = """You are a business data analyst presenting insights to a non-technical manager.

Rules:
- Use ONLY the numbers from the data and statistics provided.
- Never invent or estimate numbers.
- Be concise and business-focused.
- Highlight the most important finding first.
- 2 to 4 sentences maximum."""

    prompt = f"""Business Question: {question}

Query Results:
{data_summary}

Calculated Statistics:
{stats_str}

Write a clear business insight answering this question."""

    return generate(prompt, system)