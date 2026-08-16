from app.llm.gemini import generate

PIPELINE_STEPS = [
    {
        "step": 1,
        "name": "fetch_schema",
        "tool": "schema_tool",
        "description": "Fetch live database schema from MySQL"
    },
    {
        "step": 2,
        "name": "generate_sql",
        "tool": "sql_agent",
        "description": "Generate MySQL query from question and schema"
    },
    {
        "step": 3,
        "name": "validate_sql",
        "tool": "sql_safety",
        "description": "Validate SQL is safe before execution"
    },
    {
        "step": 4,
        "name": "execute_sql",
        "tool": "mysql_tool",
        "description": "Execute validated SQL and return results"
    },
    {
        "step": 5,
        "name": "analyze_results",
        "tool": "analyst_agent",
        "description": "Calculate statistics from query results"
    },
    {
        "step": 6,
        "name": "generate_chart",
        "tool": "chart_agent",
        "description": "Build visualization if needed"
    },
    {
        "step": 7,
        "name": "generate_answer",
        "tool": "answer_agent",
        "description": "Generate final business-focused answer"
    },
]


def _check_visualization(question: str) -> bool:
    """
    Ask LLM one yes/no question only.
    Minimal token usage — just intent detection.
    """
    system = """You are a data visualization expert.
Answer ONLY with a single word: yes or no.
No explanation. No punctuation. Just yes or no."""

    prompt = f"""Would a chart or graph help answer this business question better than just a data table?

Question: {question}"""

    response = generate(prompt, system)
    return response.strip().lower().startswith("yes")


def create_plan(question: str) -> dict:
    """
    Builds the execution plan.
    Steps are hardcoded — only visualization intent uses LLM.
    """
    requires_viz = _check_visualization(question)

    steps = [
        step for step in PIPELINE_STEPS
        if not (step["tool"] == "chart_agent" and not requires_viz)
    ]

    return {
        "question": question,
        "requires_visualization": requires_viz,
        "total_steps": len(steps),
        "steps": steps
    }