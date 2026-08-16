import json
import pandas as pd
from app.llm.gemini import generate


def decide_chart(question: str, df: pd.DataFrame) -> dict:
    """
    Uses LLM to decide the best chart type for the data.
    Returns a chart specification — rendering happens separately.
    """
    if df.empty:
        return {"required": False}

    columns = list(df.columns)
    sample = df.head(3).to_dict(orient="records")

    system = """You are a data visualization expert.
Decide the best chart type for the given data and question.

Respond ONLY with valid JSON — no markdown, no extra text:
{
  "required": true,
  "chart_type": "bar",
  "x_column": "category",
  "y_column": "revenue",
  "title": "Revenue by Category"
}

Allowed chart types: bar, line, area, pie, scatter, histogram

If no chart is needed respond with:
{"required": false}"""

    prompt = f"""Question: {question}
Columns available: {columns}
Sample data: {json.dumps(sample, default=str)}

What is the best chart for this data?"""

    response = generate(prompt, system)

    response = response.strip()
    if response.startswith("```"):
        lines = response.split("\n")
        response = "\n".join(lines[1:-1])

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"required": False}