import pandas as pd


def analyze_results(df: pd.DataFrame) -> dict:
    """
    Performs deterministic calculations on query results.
    No LLM needed — pure Python/Pandas.
    """
    if df.empty:
        return {
            "has_data": False,
            "row_count": 0,
            "stats": {}
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

        # Add percentage share per row if multiple rows
        if len(df) > 1:
            total = df[col].sum()
            if total and total > 0:
                df = df.copy()
                df[f"{col}_pct"] = round(df[col] / total * 100, 2)

    return {
        "has_data": True,
        "row_count": len(df),
        "numeric_columns": numeric_cols,
        "text_columns": text_cols,
        "stats": stats,
        "top_row": df.iloc[0].to_dict() if not df.empty else {},
        "dataframe": df  # pass enriched df forward
    }