import json
import pandas as pd
from typing import Generator
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


def stream(question: str) -> Generator[str, None, None]:
    """
    Generator that yields each pipeline step as SSE data.
    Frontend receives live updates as each agent completes.
    """

    def event(data: dict) -> str:
        """Format dict as SSE message."""
        return f"data: {json.dumps(convert_to_serializable(data))}\n\n"

    context = {
        "sql": None,
        "safety": None,
        "raw_df": pd.DataFrame(),
        "final_df": pd.DataFrame(),
        "analysis": {},
        "chart": {},
        "answer": None,
        "row_count": 0,
        "execution_time_ms": 0,
        "sql_attempts": 0,
        "error": None,
    }

    # ── Step 0: Planner ─────────────────────────────────────
    yield event({
        "type": "step",
        "step": 0,
        "name": "Planner",
        "status": "running",
    })

    plan = create_plan(question)

    yield event({
        "type": "step",
        "step": 0,
        "name": "Planner",
        "status": "done",
        "requires_visualization": plan["requires_visualization"],
        "total_steps": plan["total_steps"],
    })

    # ── Execute each step ────────────────────────────────────
    for step in plan["steps"]:
        tool = step["tool"]
        step_num = step["step"]
        step_name = step["name"]

        yield event({
            "type": "step",
            "step": step_num,
            "name": step_name,
            "status": "running",
        })

        try:

            # ── schema_tool ─────────────────────────────────
            if tool == "schema_tool":
                get_schema_for_prompt()
                yield event({
                    "type": "step",
                    "step": step_num,
                    "name": step_name,
                    "status": "done",
                })

            # ── sql_agent ───────────────────────────────────
            elif tool == "sql_agent":
                context["sql"] = generate_sql(question)
                context["sql_attempts"] = 1
                yield event({
                    "type": "step",
                    "step": step_num,
                    "name": step_name,
                    "status": "done",
                    "sql": context["sql"],
                })

            # ── sql_safety ──────────────────────────────────
            elif tool == "sql_safety":
                is_safe, reason = validate_sql(context["sql"])
                context["safety"] = {"passed": is_safe, "reason": reason}

                if not is_safe:
                    yield event({
                        "type": "step",
                        "step": step_num,
                        "name": step_name,
                        "status": "blocked",
                        "reason": reason,
                    })
                    context["error"] = f"SQL blocked: {reason}"
                    break

                yield event({
                    "type": "step",
                    "step": step_num,
                    "name": step_name,
                    "status": "done",
                })

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

                        yield event({
                            "type": "step",
                            "step": step_num,
                            "name": step_name,
                            "status": "done",
                            "rows_returned": result.get("row_count", 0),
                            "attempts": attempt,
                            "execution_time_ms": result.get("execution_time_ms", 0),
                        })
                        break

                    elif attempt < MAX_SQL_ATTEMPTS:
                        yield event({
                            "type": "step",
                            "step": step_num,
                            "name": step_name,
                            "status": f"retrying",
                            "attempt": attempt,
                            "reason": reflection["reason"],
                            "refined_sql": reflection["refined_sql"],
                        })
                        context["sql"] = reflection["refined_sql"]

                        is_safe, reason = validate_sql(context["sql"])
                        if not is_safe:
                            yield event({
                                "type": "step",
                                "step": step_num,
                                "name": step_name,
                                "status": "blocked",
                                "reason": reason,
                            })
                            context["error"] = f"Refined SQL blocked: {reason}"
                            break
                    else:
                        context["raw_df"] = raw_df
                        context["row_count"] = 0
                        yield event({
                            "type": "step",
                            "step": step_num,
                            "name": step_name,
                            "status": "max_attempts_reached",
                            "attempts": attempt,
                        })

            # ── analyst_agent ────────────────────────────────
            elif tool == "analyst_agent":
                analysis = analyze_results(context["raw_df"], question)
                context["final_df"] = analysis.pop("final_df")
                context["analysis"] = analysis

                yield event({
                    "type": "step",
                    "step": step_num,
                    "name": step_name,
                    "status": "done",
                    "stats": analysis.get("stats", {}),
                    "row_count": analysis.get("row_count", 0),
                })

            # ── chart_agent ──────────────────────────────────
            elif tool == "chart_agent":
                context["chart"] = decide_chart(
                    question,
                    context["final_df"]
                )
                yield event({
                    "type": "step",
                    "step": step_num,
                    "name": step_name,
                    "status": "done",
                    "chart_type": context["chart"].get("spec", {}).get("chart_type"),
                })

            # ── answer_agent ─────────────────────────────────
            elif tool == "answer_agent":
                context["answer"] = generate_answer(
                    question,
                    context["final_df"],
                    context["analysis"]
                )
                yield event({
                    "type": "step",
                    "step": step_num,
                    "name": step_name,
                    "status": "done",
                })

        except Exception as e:
            yield event({
                "type": "step",
                "step": step_num,
                "name": step_name,
                "status": "error",
                "error": str(e),
            })
            context["error"] = str(e)
            break

  # ── Build final response ─────────────────────────────────
    try:
        final_df = context["final_df"]
        raw_data = serialize_dataframe(final_df)
        clean_data, _ = filter_sensitive_columns(raw_data)
    except Exception as e:
        print(f"DEBUG final block error: {e}")
        clean_data = []

    final_event = convert_to_serializable({
        "type": "final",
        "success": context["error"] is None,
        "question": question,
        "answer": context["answer"],
        "data": clean_data,
        "row_count": context["row_count"],
        "execution_time_ms": context["execution_time_ms"],
        "sql": context["sql"],
        "chart": context["chart"],
        "stats": context["analysis"].get("stats", {}),
        "error": context["error"],
    })

    yield f"data: {json.dumps(final_event)}\n\n"
    yield "data: {\"type\": \"done\"}\n\n"

def run(question: str) -> dict:
    """
    Non-streaming version — collects all stream events
    and returns the final result dict.
    Used by /api/analyze endpoint.
    """
    final_result = {}
    for event_str in stream(question):
        # Parse each SSE message
        if event_str.startswith("data: "):
            data = json.loads(event_str[6:])
            if data.get("type") == "final":
                final_result = data
    return final_result