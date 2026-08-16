from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.workflow.analyst_workflow import run

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


# ─────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "AI Data Analyst is running", "docs": "/docs"}


# ─────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────
@app.post("/api/analyze", tags=["Pipeline"], summary="Run full analysis pipeline")
def analyze(request: QuestionRequest):
    """
    Runs all agents in sequence based on the execution plan.
    Each agent receives the output of the previous one.
    """
    try:
        result = run(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))