from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.db import get_db
from models.models import User, DriveDate
from routers.auth import get_current_user
from datetime import datetime, date

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    college: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    avatar_color: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class DriveDateCreate(BaseModel):
    company: str
    drive_date: str
    notes: Optional[str] = None


@router.get("/me")
async def get_profile(cu: User = Depends(get_current_user)):
    return {
        "id": cu.id,
        "name": cu.name,
        "email": cu.email,
        "college": cu.college,
        "branch": cu.branch,
        "year": cu.year,
        "phone": cu.phone,
        "bio": cu.bio,
        "linkedin": cu.linkedin,
        "github": cu.github,
        "avatar_color": cu.avatar_color or "#6366f1",
        "total_xp": cu.total_xp or 0,
        "joined": str(cu.created_at.date()) if cu.created_at else None,
    }


@router.put("/update")
async def update_profile(data: ProfileUpdate, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    for field, value in data.dict(exclude_none=True).items():
        setattr(cu, field, value)
    db.commit()
    return {"message": "Profile updated!"}


@router.put("/change-password")
async def change_password(data: PasswordChange, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    from services.auth_service import verify_password, get_password_hash
    if not verify_password(data.current_password, cu.hashed_password):
        raise HTTPException(400, "Current password is incorrect")
    if len(data.new_password) < 6:
        raise HTTPException(400, "New password must be at least 6 characters")
    cu.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password changed!"}


@router.get("/drive-dates")
async def get_drive_dates(db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    dates = db.query(DriveDate).filter(DriveDate.user_id == cu.id).order_by(DriveDate.drive_date).all()
    today = str(date.today())
    return [
        {
            "id": d.id,
            "company": d.company,
            "drive_date": d.drive_date,
            "notes": d.notes,
            "is_upcoming": d.drive_date >= today,
            "days_left": (datetime.strptime(d.drive_date, "%Y-%m-%d").date() - date.today()).days,
        }
        for d in dates
    ]


@router.post("/drive-dates")
async def add_drive_date(data: DriveDateCreate, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    drive = DriveDate(user_id=cu.id, company=data.company, drive_date=data.drive_date, notes=data.notes)
    db.add(drive)
    db.commit()
    db.refresh(drive)
    days = (datetime.strptime(data.drive_date, "%Y-%m-%d").date() - date.today()).days
    if days == 0:
        msg = f"🎯 All the best for {data.company} drive TODAY! You've got this!"
    elif days == 1:
        msg = f"⏰ {data.company} drive is TOMORROW! Final prep time!"
    elif days <= 7:
        msg = f"📅 {data.company} drive in {days} days! Keep practicing!"
    else:
        msg = f"✅ {data.company} drive set for {data.drive_date}. {days} days to prepare!"
    return {"id": drive.id, "message": msg, "days_left": days}


@router.delete("/drive-dates/{did}")
async def delete_drive_date(did: int, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    d = db.query(DriveDate).filter(DriveDate.id == did, DriveDate.user_id == cu.id).first()
    if not d:
        raise HTTPException(404, "Not found")
    db.delete(d)
    db.commit()
    return {"message": "Deleted"}
