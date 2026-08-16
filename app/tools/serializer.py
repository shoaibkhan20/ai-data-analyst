import numpy as np
import pandas as pd
from typing import Any

def convert_to_serializable(obj: Any) -> Any:
    """
    Recursively converts numpy/pandas types to
    native Python types so FastAPI can serialize them.
    """
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif pd.isna(obj) if not isinstance(obj, (list, dict)) else False:
        return None
    else:
        return obj


def serialize_dataframe(df: pd.DataFrame) -> list[dict]:
    """
    Converts a DataFrame to a JSON-serializable list of dicts.
    Handles all numpy types automatically.
    """
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    return convert_to_serializable(records)