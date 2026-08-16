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
from app.tools.serializer import serialize_dataframe, convert_to_serializable
MAX_SQL_ATTEMPTS = 3

def run(question: str) -> dict:
    plan = create_plan(question)

    context = {
        "question": question,
        # "plan": plan,
        "sql": None,
        "safety": None,
        "raw_df": pd.DataFrame(),       # flat rows from DB
        "final_df": pd.DataFrame(),     # grouped or flat — single source of truth
        "analysis": {},
        "chart": {},
        "answer": None,
        "row_count": 0,
        "execution_time_ms": 0,
        "sql_attempts": 0,
        "error": None,
    }

    trace = []

    for step in plan["steps"]:
        tool = step["tool"]
        step_num = step["step"]
        step_name = step["name"]

        trace.append({
            "step": step_num,
            "name": step_name,
            "status": "running"
        })
        try:
            # ── schema_tool ─────────────────────────────────
            if tool == "schema_tool":
                get_schema_for_prompt()
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
                result = {}

                for attempt in range(1, MAX_SQL_ATTEMPTS + 1):
                    context["sql_attempts"] = attempt

                    try:
                        result = db.execute_query(context["sql"])
                        raw_df = result["dataframe"]
                        exec_error = None
                    except Exception as e:
                        raw_df = pd.DataFrame()
                        exec_error = str(e)

                    reflection = validate_and_reflect(
                        question=question,
                        sql=context["sql"],
                        df=raw_df,
                        error=exec_error,
                        attempt=attempt,
                    )

                    if not reflection["needs_retry"]:
                        context["raw_df"] = raw_df
                        context["row_count"] = result.get("row_count", 0)
                        context["execution_time_ms"] = result.get("execution_time_ms", 0)
                        trace[-1]["status"] = "done"
                        trace[-1]["rows_returned"] = result.get("row_count", 0)
                        trace[-1]["attempts"] = attempt
                        break

                    elif attempt < MAX_SQL_ATTEMPTS:
                        trace[-1]["status"] = f"retrying (attempt {attempt})"
                        trace[-1]["retry_reason"] = reflection["reason"]
                        context["sql"] = reflection["refined_sql"]

                        is_safe, reason = validate_sql(context["sql"])
                        if not is_safe:
                            context["error"] = f"Refined SQL blocked: {reason}"
                            trace[-1]["status"] = "blocked"
                            break
                    else:
                        context["raw_df"] = raw_df
                        context["row_count"] = 0
                        trace[-1]["status"] = "max_attempts_reached"
                        trace[-1]["attempts"] = attempt

            # ── analyst_agent ────────────────────────────────
            elif tool == "analyst_agent":
                analysis = analyze_results(context["raw_df"], question)

                # final_df is the single source of truth going forward
                context["final_df"] = analysis.pop("final_df")
                context["analysis"] = analysis
                trace[-1]["status"] = "done"

            # ── chart_agent ──────────────────────────────────
            elif tool == "chart_agent":
                context["chart"] = decide_chart(
                    question,
                    context["final_df"]   # uses final_df not raw_df
                )
                trace[-1]["status"] = "done"

            # ── answer_agent ─────────────────────────────────
            elif tool == "answer_agent":
                context["answer"] = generate_answer(
                    question,
                    context["final_df"],  # uses final_df not raw_df
                    context["analysis"]
                )
                trace[-1]["status"] = "done"

        except Exception as e:
            trace[-1]["status"] = "error"
            trace[-1]["error"] = str(e)
            context["error"] = str(e)
            break

    # ── Build final response ─────────────────────────────────
    final_df = context["final_df"]
    raw_data = serialize_dataframe(final_df)
    clean_data, removed_columns = filter_sensitive_columns(raw_data)

    analysis = context["analysis"]
    return convert_to_serializable({
        "success": context["error"] is None,
        "question": question,
        "answer": context["answer"],
        "data": clean_data,
        "row_count": context["row_count"],
        "execution_time_ms": context["execution_time_ms"],
        "sql": context["sql"],
        "chart": context["chart"],
        "stats": analysis.get("stats", {}),
        "trace": trace,
        "error": context["error"],
    })