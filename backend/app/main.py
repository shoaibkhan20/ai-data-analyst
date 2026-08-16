from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agents.planner import create_plan
from app.agents.sql_agent import generate_sql
from app.tools.mysql_tool import MySQLTool
from app.tools.schema_tool import get_schema_for_prompt

app = FastAPI(
    title="AI Data Analyst",
    description="Agentic AI that converts business questions into SQL and insights",
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


@app.get("/")
def root():
    return {"status": "AI Data Analyst is running", "docs": "/docs"}

@app.post("/api/analyze", summary="Run full analysis pipeline", tags=["Pipeline"])
def analyze(request: QuestionRequest):
    """
    Runs the full pipeline in sequence:
    1. Create analysis plan
    2. Fetch live database schema
    3. Generate SQL from plan + schema
    """
    trace = []

    # Step 1 - Planner
    trace.append("Step 1: Creating analysis plan...")
    plan = create_plan(request.question)
    trace.append("Step 1: Done")

    # Step 2 - Schema
    trace.append("Step 2: Fetching live database schema...")
    schema = get_schema_for_prompt()
    trace.append("Step 2: Done")

    # Step 3 - SQL Agent
    trace.append("Step 3: Generating SQL query...")
    sql = generate_sql(request.question, plan)
    trace.append("Step 3: Done")

    return {
        "question": request.question,
        "trace": trace,
        "plan": plan,
        "sql": sql,
    }