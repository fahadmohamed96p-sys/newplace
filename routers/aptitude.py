from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database.db import get_db
from models.models import Question, TestAttempt, User
from routers.auth import get_current_user
from services.llm_service import generate_test_feedback
import random

router = APIRouter(prefix="/aptitude", tags=["aptitude"])


class AnswerItem(BaseModel):
    question_id: int
    selected_answer: str


class TestSubmit(BaseModel):
    answers: List[AnswerItem]
    time_taken: int
    test_type: str = "aptitude"


@router.get("/questions")
async def get_questions(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    count: int = 15,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Question).filter(Question.category != "coding", Question.is_active == True)
    if category and category != "all":
        query = query.filter(Question.category == category)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    questions = query.all()
    random.shuffle(questions)
    return [
        {"id": q.id, "category": q.category, "difficulty": q.difficulty,
         "question_text": q.question_text, "options": q.options, "tags": q.tags}
        for q in questions[:count]
    ]


@router.post("/submit")
async def submit_test(
    sub: TestSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not sub.answers:
        raise HTTPException(400, "No answers provided")

    q_ids = [a.question_id for a in sub.answers]
    questions = {q.id: q for q in db.query(Question).filter(Question.id.in_(q_ids)).all()}

    correct = 0
    total = len(sub.answers)
    detailed = []
    wrong = []

    for ans in sub.answers:
        q = questions.get(ans.question_id)
        if not q:
            continue
        is_correct = ans.selected_answer == q.correct_answer
        if is_correct:
            correct += 1
        else:
            wrong.append({"question": q.question_text[:80], "your_answer": ans.selected_answer, "correct": q.correct_answer})
        detailed.append({
            "question_id": ans.question_id,
            "question_text": q.question_text[:120],
            "selected": ans.selected_answer,
            "correct": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })

    percentage = (correct / total * 100) if total > 0 else 0
    xp = int(percentage / 10) * 5

    feedback = await generate_test_feedback(sub.test_type, correct, total, percentage, sub.time_taken, wrong)

    attempt = TestAttempt(
        user_id=current_user.id,
        test_type=sub.test_type,
        score=correct,
        max_score=total,
        percentage=percentage,
        time_taken=sub.time_taken,
        answers=detailed,
        feedback=feedback,
        xp_earned=xp,
        completed_at=datetime.utcnow(),
    )
    db.add(attempt)
    current_user.total_xp = (current_user.total_xp or 0) + xp
    db.commit()

    return {
        "attempt_id": attempt.id,
        "score": correct,
        "max_score": total,
        "percentage": round(percentage, 2),
        "correct": correct,
        "wrong": total - correct,
        "time_taken": sub.time_taken,
        "feedback": feedback,
        "detailed_answers": detailed,
        "xp_earned": xp,
    }
