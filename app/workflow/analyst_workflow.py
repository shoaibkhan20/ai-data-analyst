import pandas as pd
from app.agents.planner import create_plan
from app.tools.schema_tool import get_schema_for_prompt
from app.agents.sql_agent import generate_sql
from app.tools.sql_safety import validate_sql, filter_sensitive_columns
from app.tools.db_factory import get_db
from app.agents.validator import validate_and_reflect
from app.agents.analyst import analyze_results
from app.agents.chart_agent import decide_chart
from app.agents.answer_agent import generate_answer
# Add this import at the top
from app.tools.serializer import serialize_dataframe, convert_to_serializable
MAX_SQL_ATTEMPTS = 3


def run(question: str) -> dict:
    """
    Executes the full pipeline following the plan.
    Includes SQL reflection and retry loop.
    Filters sensitive columns from results.
    """

    plan = create_plan(question)

    context = {
        "question": question,
        "plan": plan,
        "schema": None,
        "sql": None,
        "safety": None,
        "dataframe": pd.DataFrame(),
        "analysis": {},
        "chart": {},
        "answer": None,
        "row_count": 0,
        "execution_time_ms": 0,
        "sql_attempts": 0,
        "removed_columns": [],
        "error": None,
    }

    trace = []

    for step in plan["steps"]:
        tool = step["tool"]
        step_name = step["name"]
        step_num = step["step"]

        trace.append({
            "step": step_num,
            "name": step_name,
            "tool": tool,
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
                context["sql_attempts"] = 1
                trace[-1]["status"] = "done"
                trace[-1]["attempt"] = 1

            # ── sql_safety ──────────────────────────────────
            elif tool == "sql_safety":
                is_safe, reason = validate_sql(context["sql"])
                context["safety"] = {"passed": is_safe, "reason": reason}

                if not is_safe:
                    trace[-1]["status"] = "blocked"
                    trace[-1]["reason"] = reason
                    context["error"] = f"SQL blocked: {reason}"
                    break

                trace[-1]["status"] = "done"

            # ── mysql_tool + reflection loop ─────────────────
            elif tool == "mysql_tool":
                db = get_db()
                exec_error = None

                for attempt in range(1, MAX_SQL_ATTEMPTS + 1):
                    context["sql_attempts"] = attempt

                    # Try executing
                    try:
                        result = db.execute_query(context["sql"])
                        df = result["dataframe"]
                        exec_error = None
                    except Exception as e:
                        df = pd.DataFrame()
                        exec_error = str(e)

                    # Reflect on the result
                    reflection = validate_and_reflect(
                        question=question,
                        sql=context["sql"],
                        df=df,
                        error=exec_error,
                        attempt=attempt,
                    )

                    if not reflection["needs_retry"]:
                        # Result is good
                        context["dataframe"] = df
                        context["row_count"] = result["row_count"]
                        context["execution_time_ms"] = result["execution_time_ms"]
                        trace[-1]["status"] = "done"
                        trace[-1]["rows_returned"] = result["row_count"]
                        trace[-1]["attempts"] = attempt
                        break

                    elif attempt < MAX_SQL_ATTEMPTS:
                        # Retry with refined SQL
                        trace[-1]["status"] = f"retrying (attempt {attempt})"
                        trace[-1]["retry_reason"] = reflection["reason"]
                        context["sql"] = reflection["refined_sql"]

                        # Validate refined SQL is safe too
                        is_safe, reason = validate_sql(context["sql"])
                        if not is_safe:
                            context["error"] = f"Refined SQL blocked: {reason}"
                            trace[-1]["status"] = "blocked"
                            break
                    else:
                        # Max attempts reached
                        context["dataframe"] = df
                        context["row_count"] = 0
                        trace[-1]["status"] = "max_attempts_reached"
                        trace[-1]["attempts"] = attempt
                        trace[-1]["last_reason"] = reflection["reason"]

            # ── analyst_agent ────────────────────────────────
            elif tool == "analyst_agent":
                context["analysis"] = analyze_results(context["dataframe"])
                trace[-1]["status"] = "done"

            # ── chart_agent ──────────────────────────────────
            elif tool == "chart_agent":
                context["chart"] = decide_chart(
                    question,
                    context["dataframe"]
                )
                trace[-1]["status"] = "done"

            # ── answer_agent ─────────────────────────────────
            elif tool == "answer_agent":
                context["answer"] = generate_answer(
                    question,
                    context["dataframe"],
                    context["analysis"]
                )
                trace[-1]["status"] = "done"

        except Exception as e:
            trace[-1]["status"] = "error"
            trace[-1]["error"] = str(e)
            context["error"] = str(e)
            break

    # ── Filter sensitive columns from results ────────────────
    df = context["dataframe"]
    raw_data = serialize_dataframe(df)
    clean_data, removed_columns = filter_sensitive_columns(raw_data)

    return convert_to_serializable({
        "success": context["error"] is None,
        "question": question,
        "trace": trace,
        "plan": plan,
        "sql": context["sql"],
        "sql_attempts": context["sql_attempts"],
        "safety": context["safety"],
        "data": clean_data,
        "row_count": context["row_count"],
        "execution_time_ms": context["execution_time_ms"],
        "analysis": context["analysis"],
        "chart": context["chart"],
        "answer": context["answer"],
        "removed_columns": removed_columns,
        "error": context["error"],
    })