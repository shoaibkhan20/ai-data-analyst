from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any
from app.workflow.analyst_workflow import run, stream
from app.agents.planner import create_plan
from app.agents.sql_agent import generate_sql
from app.agents.validator import validate_and_reflect
from app.agents.analyst import analyze_results
from app.agents.chart_agent import decide_chart
from app.agents.answer_agent import generate_answer
from app.tools.schema_tool import get_schema_for_prompt
from app.tools.sql_safety import validate_sql, filter_sensitive_columns
from app.tools.db_factory import get_db
import pandas as pd

app = FastAPI(
    title="AI Data Analyst",
    description="""
## AI Data Analyst — Agentic Pipeline

Converts natural language business questions into SQL queries and insights.

### Endpoints
- `/api/stream`  — real time SSE stream (use this in production frontend)
- `/api/analyze` — single response with full result
- `/api/agents/*` — individual agent endpoints for testing
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


class SQLRequest(BaseModel):
    question: str


class SafetyRequest(BaseModel):
    question: str
    sql: str


class ExecuteRequest(BaseModel):
    sql: str


class AnalystRequest(BaseModel):
    data: list[dict[str, Any]]


class ChartRequest(BaseModel):
    question: str
    data: list[dict[str, Any]]


class AnswerRequest(BaseModel):
    question: str
    data: list[dict[str, Any]]
    analysis: dict[str, Any]


class ReflectionRequest(BaseModel):
    question: str
    sql: str
    data: list[dict[str, Any]]
    error: str | None = None
    attempt: int = 1
# ─────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────
@app.get("/", tags=["Health"], summary="Health check")
def root():
    return {"status": "AI Data Analyst is running", "docs": "/docs"}


# ─────────────────────────────────────────
# SSE STREAM — production endpoint
# ─────────────────────────────────────────
@app.post(
    "/api/stream",
    tags=["Pipeline"],
    summary="Real time stream — SSE (use in production)",
)
def analyze_stream(request: QuestionRequest):
    """
    Streams each agent step in real time using Server-Sent Events.

    Each event is a JSON object:
    {"type": "step", "step": 1, "name": "Planner", "status": "done"}
    {"type": "step", "step": 2, "name": "SQL Agent", "status": "done", "sql": "..."}
    {"type": "final", "answer": "...", "data": [...], "chart": {...}}
    The frontend listens with EventSource and updates the UI as each step arrives.
    Connection closes automatically when pipeline finishes.
    """
    return StreamingResponse(
        stream(request.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# ─────────────────────────────────────────
# FULL PIPELINE — single response
# ─────────────────────────────────────────
@app.post(
    "/api/analyze",
    tags=["Pipeline"],
    summary="Full pipeline — single response",
)
def analyze(request: QuestionRequest):
    """
    Runs all agents and returns the complete result at once.
    Use /api/stream instead for real time frontend updates.
    """
    try:
        result = run(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────
# INDIVIDUAL AGENT ENDPOINTS
# ─────────────────────────────────────────
@app.post("/api/agents/planner", tags=["Agents"], summary="Agent 1 — Planner")
def agent_planner(request: QuestionRequest):
    try:
        plan = create_plan(request.question)
        return {"agent": "Planner", "status": "done", "output": {"plan": plan}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/schema", tags=["Agents"], summary="Agent 2 — Schema")
def agent_schema():
    try:
        schema = get_schema_for_prompt()
        return {"agent": "Schema", "status": "done", "output": {"schema": schema}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/sql", tags=["Agents"], summary="Agent 3 — SQL Agent")
def agent_sql(request: SQLRequest):
    try:
        sql = generate_sql(request.question)
        return {"agent": "SQL Agent", "status": "done", "output": {"sql": sql}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/safety", tags=["Agents"], summary="Agent 4 — SQL Safety")
def agent_safety(request: SafetyRequest):
    try:
        is_safe, reason = validate_sql(request.sql)
        return {
            "agent": "SQL Safety",
            "status": "done",
            "output": {"passed": is_safe, "reason": reason}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/execute", tags=["Agents"], summary="Agent 5 — SQL Executor")
def agent_execute(request: ExecuteRequest):
    try:
        db = get_db()
        result = db.execute_query(request.sql)
        df = result["dataframe"]
        raw_data = df.to_dict(orient="records") if not df.empty else []
        clean_data, removed = filter_sensitive_columns(raw_data)
        return {
            "agent": "SQL Executor",
            "status": "done",
            "output": {
                "data": clean_data,
                "row_count": result["row_count"],
                "execution_time_ms": result["execution_time_ms"],
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/analyst", tags=["Agents"], summary="Agent 6 — Analyst")
def agent_analyst(request: AnalystRequest):
    try:
        df = pd.DataFrame(request.data)
        analysis = analyze_results(df)
        analysis.pop("final_df", None)
        return {
            "agent": "Analyst",
            "status": "done",
            "output": {"analysis": analysis}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/chart", tags=["Agents"], summary="Agent 7 — Chart Agent")
def agent_chart(request: ChartRequest):
    try:
        df = pd.DataFrame(request.data)
        chart = decide_chart(request.question, df)
        return {
            "agent": "Chart Agent",
            "status": "done",
            "output": {"chart": chart}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/answer", tags=["Agents"], summary="Agent 8 — Answer Agent")
def agent_answer(request: AnswerRequest):
    try:
        df = pd.DataFrame(request.data)
        answer = generate_answer(request.question, df, request.analysis)
        return {
            "agent": "Answer Agent",
            "status": "done",
            "output": {"answer": answer}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/reflection", tags=["Agents"], summary="Agent 9 — SQL Reflection")
def agent_reflection(request: ReflectionRequest):
    try:
        df = pd.DataFrame(request.data)
        reflection = validate_and_reflect(
            question=request.question,
            sql=request.sql,
            df=df,
            error=request.error,
            attempt=request.attempt,
        )
        return {
            "agent": "SQL Reflection",
            "status": "done",
            "output": reflection
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))