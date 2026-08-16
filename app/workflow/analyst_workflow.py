import pandas as pd
from app.agents.planner import create_plan
from app.tools.schema_tool import get_schema_for_prompt
from app.agents.sql_agent import generate_sql
from app.tools.sql_safety import validate_sql
from app.tools.mysql_tool import MySQLTool

def run(question: str) -> dict:
    """
    Reads the plan and executes each tool in order.
    Each step receives the output of the previous one.
    """
    # ── Step 0: Build the plan ──────────────────────────────
    plan = create_plan(question)
    context = {
        "question": question,
        "plan": plan,
        "schema": None,
        "sql": None,
        "safety": None,
        "dataframe": pd.DataFrame(),
        "row_count": 0,
        "execution_time_ms": 0,
        "error": None,
    }
    trace = []
    # ── Execute each step from the plan ─────────────────────
    for step in plan["steps"]:
        tool = step["tool"]
        step_name = step["name"]
        step_num = step["step"]
        trace.append({
            "step": step_num,
            "name": step_name,
            # "tool": tool,
            "status": "running"
        })

        try:
            # ── schema_tool ─────────────────────────────────
            if tool == "schema_tool":
                context["schema"] = get_schema_for_prompt()
                trace[-1]["status"] = "done"

            # ── sql_agent ───────────────────────────────────
            elif tool == "sql_agent":
                context["sql"] = generate_sql(question)
                trace[-1]["status"] = "done"
            # ── sql_safety ──────────────────────────────────
            elif tool == "sql_safety":
                is_safe, reason = validate_sql(context["sql"])
                context["safety"] = {"passed": is_safe, "reason": reason}
                if not is_safe:
                    trace[-1]["status"] = "blocked"
                    trace[-1]["reason"] = reason
                    context["error"] = f"SQL blocked: {reason}"
                    break  # Stop pipeline
                trace[-1]["status"] = "done"
            # ── mysql_tool ──────────────────────────────────
            elif tool == "mysql_tool":
                db = MySQLTool()
                result = db.execute_query(context["sql"])
                context["dataframe"] = result["dataframe"]
                context["row_count"] = result["row_count"]
                context["execution_time_ms"] = result["execution_time_ms"]
                trace[-1]["status"] = "done"
                trace[-1]["rows_returned"] = result["row_count"]

            # ── analyst_agent ────────────────────────────────
            elif tool == "analyst_agent":
                # Coming next — placeholder for now
                trace[-1]["status"] = "coming_soon"

            # ── chart_agent ──────────────────────────────────
            elif tool == "chart_agent":
                # Coming next — placeholder for now
                trace[-1]["status"] = "coming_soon"

            # ── answer_agent ─────────────────────────────────
            elif tool == "answer_agent":
                # Coming next — placeholder for now
                trace[-1]["status"] = "coming_soon"

        except Exception as e:
            trace[-1]["status"] = "error"
            trace[-1]["error"] = str(e)
            context["error"] = str(e)
            break  # Stop pipeline on error

    # ── Build final response ─────────────────────────────────
    df = context["dataframe"]

    return {
        "success": context["error"] is None,
        "question": question,
        "trace": trace,
        # "plan": plan,
        "sql": context["sql"],
        "safety": context["safety"],
        "data": df.to_dict(orient="records") if not df.empty else [],
        "row_count": context["row_count"],
        "execution_time_ms": context["execution_time_ms"],
        "error": context["error"],
    }