import json
import pandas as pd
from app.llm.gemini import generate
from app.tools.serializer import convert_to_serializable


def generate_answer(
    question: str,
    df: pd.DataFrame,
    analysis: dict,
) -> str:
    """
    Generates a business-focused answer from the final dataframe.
    The df here is already grouped if grouping was applied.
    """
    if df.empty or not analysis.get("has_data"):
        return "No data was found to answer this question."

    stats = analysis.get("stats", {})

    # If no numeric stats — data is categorical/grouped
    # Return a natural language summary instead
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

    # Numeric data — use stats for the answer
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
- 2 to 4 sentences maximum."""

    prompt = f"""Business Question: {question}

Query Results:
{data_summary}

Calculated Statistics:
{stats_str}

Write a clear business insight answering this question."""

    return generate(prompt, system)