import json
from app.llm.gemini import generate


def create_plan(question: str) -> dict:
    system = """You are a data analysis planner.
Given a business question, create a structured analysis plan.

Respond ONLY with valid JSON in this exact format:
{
  "goal": "one sentence describing what we are finding",
  "steps": ["step 1", "step 2", "step 3"],
  "requires_visualization": true
}

No extra text. No markdown. Just the JSON object."""

    prompt = f"""Business Question: {question}

Create a structured analysis plan."""

    response = generate(prompt, system)

    response = response.strip()
    if response.startswith("```"):
        lines = response.split("\n")
        response = "\n".join(lines[1:-1])

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "goal": f"Answer: {question}",
            "steps": ["Analyze the question", "Generate SQL", "Execute query"],
            "requires_visualization": False,
        }