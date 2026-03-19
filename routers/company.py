from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database.db import get_db
from models.models import CompanyQuestion, TestAttempt, User
from routers.auth import get_current_user
import random

router = APIRouter(prefix="/company", tags=["company"])

COMPANIES = [
    {"id": "tcs",          "name": "TCS",           "color": "#0052cc", "logo": "T", "full_name": "Tata Consultancy Services"},
    {"id": "infosys",      "name": "Infosys",        "color": "#007cc3", "logo": "I", "full_name": "Infosys Technologies"},
    {"id": "wipro",        "name": "Wipro",          "color": "#8b1a1a", "logo": "W", "full_name": "Wipro Limited"},
    {"id": "zoho",         "name": "Zoho",           "color": "#e03c31", "logo": "Z", "full_name": "Zoho Corporation"},
    {"id": "accenture",    "name": "Accenture",      "color": "#a100ff", "logo": "A", "full_name": "Accenture"},
    {"id": "cognizant",    "name": "Cognizant",      "color": "#0033a0", "logo": "C", "full_name": "Cognizant Technology"},
    {"id": "hcl",          "name": "HCL",            "color": "#00a651", "logo": "H", "full_name": "HCL Technologies"},
    {"id": "techmahindra", "name": "TechMahindra",   "color": "#cc0000", "logo": "M", "full_name": "Tech Mahindra"},
]


class AnswerItem(BaseModel):
    question_id: int
    selected_answer: str


class CompanySubmit(BaseModel):
    answers: List[AnswerItem]
    company: str
    time_taken: int


@router.get("/list")
async def list_companies(db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    result = []
    for c in COMPANIES:
        count = db.query(CompanyQuestion).filter(
            CompanyQuestion.company == c["id"],
            CompanyQuestion.is_active == True,
        ).count()
        result.append({**c, "question_count": count})
    return result


@router.get("/{company}/questions")
async def get_company_questions(
    company: str,
    category: Optional[str] = None,
    count: int = 15,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user),
):
    query = db.query(CompanyQuestion).filter(
        CompanyQuestion.company == company.lower(),
        CompanyQuestion.is_active == True,
    )
    if category:
        query = query.filter(CompanyQuestion.category == category)
    qs = query.all()
    random.shuffle(qs)
    qs = qs[:count]
    return [
        {"id": q.id, "category": q.category, "difficulty": q.difficulty,
         "question_text": q.question_text, "options": q.options, "tags": q.tags, "year": q.year}
        for q in qs
    ]


@router.post("/submit")
async def submit_company(
    sub: CompanySubmit,
    db: Session = Depends(get_db),
    cu: User = Depends(get_current_user),
):
    q_ids = [a.question_id for a in sub.answers]
    questions = {q.id: q for q in db.query(CompanyQuestion).filter(CompanyQuestion.id.in_(q_ids)).all()}

    correct = 0
    total = len(sub.answers)
    detailed = []

    for ans in sub.answers:
        q = questions.get(ans.question_id)
        if not q:
            continue
        is_correct = ans.selected_answer == q.correct_answer
        if is_correct:
            correct += 1
        detailed.append({
            "question_id": ans.question_id,
            "question_text": q.question_text[:100],
            "selected": ans.selected_answer,
            "correct": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })

    percentage = (correct / total * 100) if total > 0 else 0
    xp = int(percentage / 10) * 8

    attempt = TestAttempt(
        user_id=cu.id,
        test_type=f"company_{sub.company}",
        score=correct,
        max_score=total,
        percentage=percentage,
        time_taken=sub.time_taken,
        answers=detailed,
        feedback=f"{sub.company.upper()} mock: {correct}/{total} ({percentage:.1f}%)",
        xp_earned=xp,
        completed_at=datetime.utcnow(),
    )
    db.add(attempt)
    cu.total_xp = (cu.total_xp or 0) + xp
    db.commit()

    return {
        "score": correct,
        "max_score": total,
        "percentage": round(percentage, 2),
        "correct": correct,
        "wrong": total - correct,
        "detailed_answers": detailed,
        "xp_earned": xp,
    }
