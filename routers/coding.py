from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database.db import get_db
from models.models import Question, TestAttempt, User
from routers.auth import get_current_user
from services.code_executor import execute_code, run_test_cases

router = APIRouter(prefix="/coding", tags=["coding"])


class RunRequest(BaseModel):
    source_code: str
    language: str = "python"
    stdin: Optional[str] = ""


class SubmitRequest(BaseModel):
    question_id: int
    source_code: str
    language: str = "python"
    time_taken: int = 0


@router.get("/questions")
async def get_questions(
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Question).filter(Question.category == "coding", Question.is_active == True)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    qs = query.all()
    return [
        {"id": q.id, "category": q.category, "difficulty": q.difficulty,
         "question_text": q.question_text, "starter_code": q.starter_code, "tags": q.tags}
        for q in qs
    ]


@router.post("/run")
async def run_code(req: RunRequest, current_user: User = Depends(get_current_user)):
    return await execute_code(req.source_code, req.language, req.stdin or "")


@router.post("/submit")
async def submit_code(
    req: SubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Question).filter(Question.id == req.question_id, Question.category == "coding").first()
    if not q:
        raise HTTPException(404, "Question not found")
    if not q.test_cases:
        raise HTTPException(400, "No test cases for this question")

    results = await run_test_cases(req.source_code, req.language, q.test_cases)
    xp = int(results["percentage"] / 10) * 10

    attempt = TestAttempt(
        user_id=current_user.id,
        test_type="coding",
        score=results["passed"],
        max_score=results["total"],
        percentage=results["percentage"],
        time_taken=req.time_taken,
        answers={"question_id": req.question_id, "language": req.language, "test_results": results["results"]},
        feedback=f"Passed {results['passed']}/{results['total']} ({results['percentage']:.1f}%)",
        xp_earned=xp,
        completed_at=datetime.utcnow(),
    )
    db.add(attempt)
    current_user.total_xp = (current_user.total_xp or 0) + xp
    db.commit()

    return {
        "attempt_id": attempt.id,
        "passed": results["passed"],
        "total": results["total"],
        "percentage": round(results["percentage"], 2),
        "test_results": results["results"],
        "xp_earned": xp,
    }
