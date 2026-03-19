from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database.db import get_db
from models.models import TestAttempt, CommunicationAttempt, User
from routers.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid = current_user.id
    attempts = db.query(TestAttempt).filter(TestAttempt.user_id == uid).all()
    comm = db.query(CommunicationAttempt).filter(CommunicationAttempt.user_id == uid).all()

    apt = [a for a in attempts if a.test_type in ("aptitude", "quantitative", "logical")]
    cod = [a for a in attempts if a.test_type == "coding"]
    company = [a for a in attempts if a.test_type.startswith("company_")]

    week_ago = datetime.utcnow() - timedelta(days=7)

    def avg(lst):
        vals = [i.percentage for i in lst if i.percentage is not None]
        return sum(vals) / len(vals) if vals else 0

    def best(lst):
        vals = [i.percentage for i in lst if i.percentage is not None]
        return max(vals, default=0)

    last_apt = apt[-1] if apt else None
    last_cod = cod[-1] if cod else None
    last_com = comm[-1] if comm else None

    total_time = sum(a.time_taken or 0 for a in attempts) / 60
    total_time += sum(a.duration_seconds or 0 for a in comm) / 60

    return {
        "user": {
            "name": current_user.name,
            "email": current_user.email,
            "college": current_user.college,
            "branch": current_user.branch,
            "year": current_user.year,
            "total_xp": current_user.total_xp or 0,
            "avatar_color": current_user.avatar_color,
        },
        "summary": {
            "total_tests": len(attempts) + len(comm),
            "aptitude_tests": len(apt),
            "coding_tests": len(cod),
            "communication_tests": len(comm),
            "company_tests": len(company),
            "total_time_minutes": round(total_time, 1),
        },
        "scores": {
            "aptitude_avg": round(avg(apt), 1),
            "aptitude_best": round(best(apt), 1),
            "coding_avg": round(avg(cod), 1),
            "coding_best": round(best(cod), 1),
            "communication_avg": round(
                sum(a.overall_score or 0 for a in comm) / len(comm) * 10 if comm else 0, 1
            ),
            "communication_best": round(
                max((a.overall_score or 0 for a in comm), default=0) * 10, 1
            ),
        },
        "recent_activity": {
            "aptitude_this_week": len([a for a in apt if a.started_at and a.started_at > week_ago]),
            "coding_this_week": len([a for a in cod if a.started_at and a.started_at > week_ago]),
            "communication_this_week": len([a for a in comm if a.created_at and a.created_at > week_ago]),
        },
        "trends": {
            "aptitude": [
                {"date": str(a.started_at.date()), "score": a.percentage}
                for a in sorted(apt, key=lambda x: x.started_at)[-10:]
                if a.percentage is not None
            ],
            "coding": [
                {"date": str(a.started_at.date()), "score": a.percentage}
                for a in sorted(cod, key=lambda x: x.started_at)[-10:]
                if a.percentage is not None
            ],
        },
        "last_attempts": {
            "aptitude": {
                "score": last_apt.percentage,
                "date": str(last_apt.started_at.date()),
                "feedback": last_apt.feedback,
            } if last_apt else None,
            "coding": {
                "score": last_cod.percentage,
                "date": str(last_cod.started_at.date()),
            } if last_cod else None,
            "communication": {
                "score": (last_com.overall_score or 0) * 10,
                "date": str(last_com.created_at.date()),
                "topic": last_com.topic,
            } if last_com else None,
        },
    }
