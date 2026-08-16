import json
import pandas as pd
import plotly.express as px


def render_chart(spec: dict, df: pd.DataFrame) -> dict:
    """
    Takes a chart spec from chart_agent and a DataFrame,
    renders a Plotly chart and returns it as JSON.
    Returns empty dict if chart is not required or fails.
    """
    if not spec.get("required") or df.empty:
        return {}

    chart_type = spec.get("chart_type", "bar")
    x_col = spec.get("x_column")
    y_col = spec.get("y_column")
    title = spec.get("title", "Chart")

    # Validate columns exist in dataframe
    if x_col and x_col not in df.columns:
        return {"error": f"Column '{x_col}' not found in data"}
    if y_col and y_col not in df.columns:
        return {"error": f"Column '{y_col}' not found in data"}

    try:
        if chart_type == "bar":
            fig = px.bar(df, x=x_col, y=y_col, title=title)
        elif chart_type == "line":
            fig = px.line(df, x=x_col, y=y_col, title=title)
        elif chart_type == "area":
            fig = px.area(df, x=x_col, y=y_col, title=title)
        elif chart_type == "pie":
            fig = px.pie(df, names=x_col, values=y_col, title=title)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x_col, y=y_col, title=title)
        elif chart_type == "histogram":
            col = y_col or x_col
            fig = px.histogram(df, x=col, title=title)
        else:
            fig = px.bar(df, x=x_col, y=y_col, title=title)

        return json.loads(fig.to_json())

    except Exception as e:
        return {"error": str(e)}