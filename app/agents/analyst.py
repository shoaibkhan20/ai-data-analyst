import pandas as pd
from app.tools.serializer import convert_to_serializable

def _group_by_category(df: pd.DataFrame) -> list[dict] | None:
    """
    Detects if results have a text column + multiple value columns
    and groups them into nested format.
    Example: { artistName: "AC/DC", tracks: ["Track1", "Track2"] }
    """
    if df.empty or len(df.columns) < 2:
        return None

    text_cols = df.select_dtypes(include="object").columns.tolist()
    other_cols = [c for c in df.columns if c not in text_cols]

    # Need exactly one grouping column
    if len(text_cols) != 1:
        return None

    group_col = text_cols[0]

    # If only one other column — group its values into a list
    if len(other_cols) == 1:
        value_col = other_cols[0]
        grouped = (
            df.groupby(group_col)[value_col]
            .apply(list)
            .reset_index()
        )
        grouped.columns = [group_col, f"{value_col}s"]
        return convert_to_serializable(
            grouped.to_dict(orient="records")
        )

    # If multiple other columns — group full row dicts into a list
    result = []
    for group_val, group_df in df.groupby(group_col):
        rows = group_df.drop(columns=[group_col]).to_dict(orient="records")
        result.append({
            group_col: group_val,
            "items": convert_to_serializable(rows)
        })
    return result


def analyze_results(df: pd.DataFrame) -> dict:
    """
    Performs deterministic calculations on query results.
    No LLM needed — pure Python/Pandas.
    """
    if df.empty:
        return {
            "has_data": False,
            "row_count": 0,
            "stats": {},
            "grouped_data": None,
        }

    stats = {}
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    text_cols = df.select_dtypes(include="object").columns.tolist()

    for col in numeric_cols:
        stats[col] = {
            "total": round(float(df[col].sum()), 2),
            "average": round(float(df[col].mean()), 2),
            "max": round(float(df[col].max()), 2),
            "min": round(float(df[col].min()), 2),
            "median": round(float(df[col].median()), 2),
        }

        if len(df) > 1:
            total = df[col].sum()
            if total and total > 0:
                df = df.copy()
                df[f"{col}_pct"] = round(df[col] / total * 100, 2)

    top_row = convert_to_serializable(df.iloc[0].to_dict())

    # Try to group results into nested format
    grouped = _group_by_category(df)

    return {
        "has_data": True,
        "row_count": int(len(df)),
        "numeric_columns": numeric_cols,
        "text_columns": text_cols,
        "stats": stats,
        "top_row": top_row,
        "grouped_data": grouped,
    }