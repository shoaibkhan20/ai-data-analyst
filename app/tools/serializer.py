import numpy as np
import pandas as pd
from decimal import Decimal
from typing import Any


def convert_to_serializable(obj: Any) -> Any:
    """
    Recursively converts numpy/pandas/decimal types to
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
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, float) and np.isnan(obj):
        return None
    else:
        try:
            if pd.isna(obj):
                return None
        except (TypeError, ValueError):
            pass
        return obj


def serialize_dataframe(df: pd.DataFrame) -> list[dict]:
    """
    Converts a DataFrame to a JSON-serializable list of dicts.
    Handles all numpy and decimal types automatically.
    """
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    return convert_to_serializable(records)