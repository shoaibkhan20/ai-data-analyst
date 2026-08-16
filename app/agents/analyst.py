import json
import pandas as pd
from app.llm.gemini import generate
from app.tools.serializer import convert_to_serializable


def _calculate_stats(df: pd.DataFrame) -> dict:
    """
    Pure Python stats — never use LLM for math.
    """
    stats = {}
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    for col in numeric_cols:
        stats[col] = {
            "total": round(float(df[col].sum()), 2),
            "average": round(float(df[col].mean()), 2),
            "max": round(float(df[col].max()), 2),
            "min": round(float(df[col].min()), 2),
            "median": round(float(df[col].median()), 2),
        }

    return stats


def _should_group(question: str, df: pd.DataFrame) -> bool:
    """
    Ask LLM whether the results should be grouped.
    Only called when there are exactly two text columns
    and zero numeric columns — otherwise grouping never makes sense.
    """
    text_cols = df.select_dtypes(include="object").columns.tolist()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # Grouping only makes sense for pure text results
    if len(text_cols) != 2 or len(numeric_cols) != 0:
        return False

    system = """You are a data presentation expert.
Answer ONLY with a single word: yes or no.
No explanation. No punctuation. Just yes or no."""

    prompt = f"""The user asked: "{question}"

The result has two columns: {text_cols[0]} and {text_cols[1]}

Should these results be grouped so that each unique {text_cols[0]}
has a list of its {text_cols[1]} values?

Example of grouped format:
{text_cols[0]}: "AC/DC", {text_cols[1]}s: ["Track1", "Track2"]

Answer yes or no."""

    response = generate(prompt, system)
    return response.strip().lower().startswith("yes")


def _group_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups two text columns into nested format.
    """
    text_cols = df.select_dtypes(include="object").columns.tolist()
    group_col = text_cols[0]
    value_col = text_cols[1]

    grouped = (
        df.groupby(group_col, sort=False)[value_col]
        .apply(list)
        .reset_index()
    )
    grouped.columns = [group_col, f"{value_col}s"]
    return grouped


def analyze_results(df: pd.DataFrame, question: str = "") -> dict:
    """
    Analyzes query results.
    - Stats: always Python (accurate)
    - Grouping: LLM decides based on question intent
    """
    if df.empty:
        return {
            "has_data": False,
            "row_count": 0,
            "stats": {},
            "top_row": {},
            "final_df": df,
        }

    # Always calculate stats with Python
    stats = _calculate_stats(df)

    # Ask LLM if grouping makes sense for this question
    if question and _should_group(question, df):
        final_df = _group_results(df)
    else:
        final_df = df

    top_row = convert_to_serializable(final_df.iloc[0].to_dict())

    return {
        "has_data": True,
        "row_count": int(len(final_df)),
        "stats": stats,
        "top_row": top_row,
        "final_df": final_df,
    }