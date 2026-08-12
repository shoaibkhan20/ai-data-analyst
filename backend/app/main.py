from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agents.planner import create_plan

app = FastAPI(
    title="AI Data Analyst",
    description="Agentic AI that converts business questions into SQL and insights",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI (alternative)
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


@app.post("/api/plan", summary="Generate analysis plan", tags=["Planner Agent"])
def get_plan(request: QuestionRequest):
    """
    Takes a business question and returns a structured analysis plan.
    The plan includes a goal, steps, and whether visualization is needed.
    """
    plan = create_plan(request.question)
    return {
        "question": request.question,
        "plan": plan
    }