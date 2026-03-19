from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.db import get_db
from models.models import CommunicationAttempt, User
from routers.auth import get_current_user
from services.llm_service import analyze_communication
import random

router = APIRouter(prefix="/communication", tags=["communication"])

TOPICS = [
    "Tell me about yourself",
    "Why do you want to work in the IT industry?",
    "What are your strengths and weaknesses?",
    "Describe a challenging situation you faced and how you handled it",
    "Where do you see yourself in 5 years?",
    "Why should we hire you?",
    "Describe your final year project",
    "What motivates you to work hard?",
    "How do you handle pressure and tight deadlines?",
    "What do you know about our company?",
    "Tell me about a time you worked in a team",
    "What is your greatest achievement?",
]

FILLER_WORDS = [
    "um", "uh", "er", "ah", "like", "you know", "basically",
    "actually", "literally", "so basically", "right", "okay so",
    "kind of", "sort of",
]


class CommSubmit(BaseModel):
    transcript: str
    topic: str
    duration_seconds: int
    words_per_minute: Optional[float] = None


@router.get("/topics")
async def get_topics(current_user: User = Depends(get_current_user)):
    return {"topics": random.sample(TOPICS, min(6, len(TOPICS)))}


@router.post("/analyze")
async def analyze_speech(
    sub: CommSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lower = sub.transcript.lower()
    words = lower.split()
    word_count = len(words)

    wpm = sub.words_per_minute
    if not wpm and sub.duration_seconds > 0:
        wpm = (word_count / sub.duration_seconds) * 60
    wpm = wpm or 0

    filler_found = []
    for f in FILLER_WORDS:
        count = lower.count(f" {f} ") + lower.count(f" {f}.")
        filler_found.extend([f] * count)

    analysis = await analyze_communication(sub.topic, sub.transcript, wpm, filler_found, sub.duration_seconds)

    attempt = CommunicationAttempt(
        user_id=current_user.id,
        transcript=sub.transcript,
        topic=sub.topic,
        words_per_minute=wpm,
        filler_word_count=len(filler_found),
        fluency_score=analysis["fluency_score"],
        overall_score=analysis["overall_score"],
        feedback=analysis["feedback"],
        duration_seconds=sub.duration_seconds,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "fluency_score": analysis["fluency_score"],
        "vocabulary_score": analysis["vocabulary_score"],
        "overall_score": analysis["overall_score"],
        "words_per_minute": round(wpm, 1),
        "filler_word_count": len(filler_found),
        "filler_words_found": list(set(filler_found)),
        "feedback": analysis["feedback"],
    }


@router.get("/history")
async def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    attempts = (
        db.query(CommunicationAttempt)
        .filter(CommunicationAttempt.user_id == current_user.id)
        .order_by(CommunicationAttempt.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {"id": a.id, "topic": a.topic, "overall_score": a.overall_score,
         "wpm": a.words_per_minute, "filler_count": a.filler_word_count,
         "date": str(a.created_at.date()) if a.created_at else None}
        for a in attempts
    ]
